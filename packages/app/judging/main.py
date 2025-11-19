import asyncio
import os
import sys

# 加载环境变量
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from load_env import load_env
load_env()

import agentscope
from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.pipeline import fanout_pipeline

# 导入 hook 以便消息能显示在 Studio 界面
sys.path.append(os.path.join(os.path.dirname(__file__), '../friday'))
from hook import studio_pre_print_hook, studio_post_reply_hook

# 1. 创建不同 Qwen 系列模型实例
# API Key 从环境变量读取
def create_models():
    # 从环境变量获取 DashScope API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DASHSCOPE_API_KEY 环境变量。\n"
            "请在项目根目录创建 .env 文件并添加：DASHSCOPE_API_KEY=your-api-key"
        )
    
    # Qwen-Max 模型 - 最强性能
    qwen_max_model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=api_key,
    )

    # Qwen-Plus 模型 - 性能均衡
    qwen_plus_model = DashScopeChatModel(
        model_name="qwen-plus",
        api_key=api_key,
    )

    # Qwen-Turbo 模型 - 速度优先
    qwen_turbo_model = DashScopeChatModel(
        model_name="qwen-turbo",
        api_key=api_key,
    )

    return qwen_max_model, qwen_plus_model, qwen_turbo_model

# 2. 定义判题智能体
judge_sys_prompt = "你是一位严格的题目评分专家，请根据标准对答案进行0-100分的打分，并给出理由。请以如下格式回复：\n分数: [0-100之间的整数]\n理由: [简要说明]"

def create_judging_agents(qwen_max_model, qwen_plus_model, qwen_turbo_model):
    agent_qwen_max = ReActAgent(
        name="QwenMax_Judge",
        sys_prompt=judge_sys_prompt,
        model=qwen_max_model,
        formatter=DashScopeChatFormatter(),
    )

    agent_qwen_plus = ReActAgent(
        name="QwenPlus_Judge",
        sys_prompt=judge_sys_prompt,
        model=qwen_plus_model,
        formatter=DashScopeChatFormatter(),
    )

    agent_qwen_turbo = ReActAgent(
        name="QwenTurbo_Judge",
        sys_prompt=judge_sys_prompt,
        model=qwen_turbo_model,
        formatter=DashScopeChatFormatter(),
    )

    return [agent_qwen_max, agent_qwen_plus, agent_qwen_turbo]

# 3. 协调器函数 - 核心决策逻辑
async def coordinator_agent(problem_msg: Msg, studio_url: str) -> Msg:
    """协调多个判题Agent并处理冲突"""
    
    # 获取所有 Qwen 系列模型
    qwen_max_model, qwen_plus_model, qwen_turbo_model = create_models()
    
    # 创建判题Agent列表
    judging_agents = create_judging_agents(qwen_max_model, qwen_plus_model, qwen_turbo_model)
    
    # 注册 hook，让所有 Agent 的输出都显示在 Studio
    studio_pre_print_hook.url = studio_url
    for agent in judging_agents:
        agent.register_class_hook(
            "pre_print",
            "studio_pre_print_hook",
            studio_pre_print_hook
        )
        agent.register_class_hook(
            "post_reply",
            "studio_post_reply_hook",
            studio_post_reply_hook
        )
    
    # 创建系统通知 Agent 用于发送状态消息
    system_agent = ReActAgent(
        name="System",
        sys_prompt="你是判题系统的协调器，负责通知用户当前状态",
        model=qwen_max_model,
        formatter=DashScopeChatFormatter(),
    )
    system_agent.register_class_hook(
        "pre_print",
        "studio_pre_print_hook",
        studio_pre_print_hook
    )
    system_agent.register_class_hook(
        "post_reply",
        "studio_post_reply_hook",
        studio_post_reply_hook
    )
    
    # 发送开始判题消息
    await system_agent(Msg(
        name="User",
        content="开始并行判题...",
        role="user"
    ))
    
    # Step 1: 并发执行所有判题Agent
    try:
        judge_results = await fanout_pipeline(
            agents=judging_agents,
            msg=problem_msg,
            enable_gather=True  # 启用并发
        )
    except Exception as e:
        return Msg("System", f"判题过程出错: {str(e)}", "assistant")
    
    # Step 2: 解析每个Agent的评分
    scores = []
    detailed_results = []
    
    for result in judge_results:
        content = result.get_text_content() or ""
        score_line = [line for line in content.split('\n') if '分数:' in line]
        reason_line = [line for line in content.split('\n') if '理由:' in line]
        
        if score_line:
            try:
                score = int(score_line[0].split(':')[1].strip())
                scores.append(score)
                reason = reason_line[0].split(':')[1].strip() if reason_line else "未提供"
                detailed_results.append(f"{result.name}: {score}分 (理由: {reason})")
            except ValueError:
                # 如果某个Agent评分无效，可以给一个默认值或跳过
                scores.append(50)  # 给个中位数作为容错
                detailed_results.append(f"{result.name}: 解析失败，使用默认50分")
        else:
            scores.append(50)
            detailed_results.append(f"{result.name}: 格式错误，使用默认50分")
    
    # Step 3: 判断是否冲突 (分差大于10分视为冲突)
    if len(scores) == 0:
        return Msg("System", "所有判题Agent均未能返回有效评分。", "assistant")
        
    max_score, min_score = max(scores), min(scores)
    
    if max_score - min_score > 10:
        # 发送冲突消息到 Studio
        conflict_info = (
            f"判题结果冲突: 最高{max_score}分，最低{min_score}分，"
            f"分差{max_score-min_score}分 > 10分，已转交人工处理。\n\n"
            f"详细评分:\n{chr(10).join(detailed_results)}"
        )
        
        # 通过 system_agent 发送冲突信息，让它显示在 Studio
        await system_agent(Msg(
            name="User",
            content=conflict_info,
            role="user"
        ))
        
        # Step 4: 转交人工 - 使用 UserAgent 接收输入
        user_agent = UserAgent(name="Human_Judge")
        user_agent.register_class_hook(
            "pre_print",
            "studio_pre_print_hook",
            studio_pre_print_hook
        )
        user_agent.register_class_hook(
            "post_reply",
            "studio_post_reply_hook",
            studio_post_reply_hook
        )
        
        # 发送提示消息并等待人工输入
        human_decision_msg = await user_agent(Msg(
            name="System",
            content="请人工裁定最终分数（请输入一个0-100的整数）：",
            role="system"
        ))
        
        final_score_str = human_decision_msg.get_text_content().strip()
        try:
            final_score = int(final_score_str)
            if 0 <= final_score <= 100:
                return Msg(
                    "Coordinator", 
                    f"最终得分: {final_score}分 (经人工裁定)\n详细记录: {'；'.join(detailed_results)}",
                    "assistant"
                )
            else:
                return Msg("System", f"人工输入的分数 {final_score} 不在0-100范围内，判题失败。", "assistant")
        except ValueError:
            return Msg("System", f"人工输入 '{final_score_str}' 不是有效数字，判题失败。", "assistant")
    
    else:
        # 无冲突，取平均分
        avg_score = sum(scores) / len(scores)
        result_msg = (
            f"最终得分: {avg_score:.1f}分 (各评委意见一致)\n"
            f"详细记录: {'; '.join(detailed_results)}"
        )
        
        # 通过 system_agent 发送最终结果，让它显示在 Studio
        await system_agent(Msg(
            name="User",
            content=result_msg,
            role="user"
        ))
        
        return Msg(
            "Coordinator", 
            result_msg,
            "assistant"
        )

# 4. 主函数 - 接收用户提交的题目
async def main():
    studio_url = "http://localhost:3000"
    
    # 初始化 AgentScope 并连接到 Studio
    agentscope.init(
        project="judging_system",
        name="multi_llm_judging",
        studio_url=studio_url,
        # save_log=True,
    )
    
    # 设置 hook URL
    studio_pre_print_hook.url = studio_url
    
    # 创建 UserAgent 接收用户输入的题目和答案
    user_input_agent = UserAgent(name="Student")
    user_input_agent.register_class_hook(
        "pre_print",
        "studio_pre_print_hook",
        studio_pre_print_hook
    )
    user_input_agent.register_class_hook(
        "post_reply",
        "studio_post_reply_hook",
        studio_post_reply_hook
    )
    
    # 接收用户输入
    problem_and_answer = await user_input_agent(Msg(
        name="System",
        content="请输入需要判题的题目和答案（格式：题目：XXX\n答案：XXX）：",
        role="system"
    ))
    
    # 启动判题流程
    final_result = await coordinator_agent(problem_and_answer, studio_url)
    
    # 创建结果展示 Agent
    result_agent = ReActAgent(
        name="FinalResult",
        sys_prompt="你负责展示最终判题结果",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
        ),
        formatter=DashScopeChatFormatter(),
    )
    result_agent.register_class_hook(
        "pre_print",
        "studio_pre_print_hook",
        studio_pre_print_hook
    )
    result_agent.register_class_hook(
        "post_reply",
        "studio_post_reply_hook",
        studio_post_reply_hook
    )
    
    # 显示最终结果
    await result_agent(Msg(
        name="User",
        content=final_result.content,
        role="user"
    ))

# 运行主程序
if __name__ == "__main__":
    asyncio.run(main())
