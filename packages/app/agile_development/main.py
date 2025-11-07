#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
敏捷开发 Agent 工作流主程序
"""
import asyncio
import os
import agentscope
from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg

# 导入 hook 以便消息能显示在 Studio 界面
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../friday'))
from hook import studio_pre_print_hook, studio_post_reply_hook


def create_models():
    """创建不同 Qwen 系列模型实例"""
    # 从环境变量获取 DashScope API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DASHSCOPE_API_KEY 环境变量。\n"
            "请设置环境变量：export DASHSCOPE_API_KEY='your-api-key'"
        )
    
    # Qwen-Max 模型 - 最强性能 (产品经理使用)
    qwen_max_model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=api_key,
    )

    # Qwen-Plus 模型 - 性能均衡 (架构师和测试工程师使用)
    qwen_plus_model = DashScopeChatModel(
        model_name="qwen-plus",
        api_key=api_key,
    )

    # Qwen-Turbo 模型 - 速度优先 (开发工程师使用)
    qwen_turbo_model = DashScopeChatModel(
        model_name="qwen-turbo",
        api_key=api_key,
    )

    return qwen_max_model, qwen_plus_model, qwen_turbo_model


def create_agents(qwen_max_model, qwen_plus_model, qwen_turbo_model, studio_url):
    """创建各个角色的 Agent"""
    # 产品经理 Agent (使用 qwen-max)
    product_manager = ReActAgent(
        name="ProductManager_qwen-max",
        sys_prompt="""你是一位经验丰富的产品经理，请分析用户需求并生成清晰的用户故事和验收标准。
        
        # 职责
        - 理解用户需求背景和目标
        - 将需求分解为具体的用户故事
        - 为每个用户故事编写明确的验收标准
        - 确保需求的完整性和可实现性
        
        # 输出格式
        使用以下格式输出:
        ## 用户故事
        作为[角色], 我想要[功能], 以便于[价值]
        
        ## 验收标准
        - [具体可验证的标准1]
        - [具体可验证的标准2]
        """,
        model=qwen_max_model,
        formatter=DashScopeChatFormatter(),
    )

    # 架构师 Agent (使用 qwen-plus)
    architect = ReActAgent(
        name="Architect_qwen-plus",
        sys_prompt="""你是一位资深的系统架构师，请基于产品经理提供的需求文档进行系统设计。
        
        # 职责
        - 设计系统整体架构和技术方案
        - 选择合适的技术栈和框架
        - 评估技术风险并提供解决方案
        - 编写详细的技术设计文档
        
        # 输出格式
        使用以下格式输出:
        ## 系统架构设计
        [简要描述系统架构]
        
        ## 技术选型
        - [技术1]: [选型理由]
        - [技术2]: [选型理由]
        
        ## 模块设计
        - [模块1]: [功能描述]
        - [模块2]: [功能描述]
        """,
        model=qwen_plus_model,
        formatter=DashScopeChatFormatter(),
    )

    # 开发工程师 Agent (使用 qwen-turbo)
    developer = ReActAgent(
        name="Developer_qwen-turbo",
        sys_prompt="""你是一位经验丰富的开发工程师，请根据架构师的设计文档实现代码。
        
        # 职责
        - 根据技术设计文档编写高质量代码
        - 解决具体的技术实现问题
        - 确保代码的可读性和可维护性
        - 编写必要的注释和文档
        
        # 输出格式
        使用以下格式输出:
        ## 实现方案
        [简要描述实现思路]
        
        ## 核心代码
        ```[编程语言]
        [具体代码实现]
        ```
        
        ## 代码说明
        - [要点1]: [说明]
        - [要点2]: [说明]
        """,
        model=qwen_turbo_model,
        formatter=DashScopeChatFormatter(),
    )

    # 测试工程师 Agent (使用 qwen-plus)
    tester = ReActAgent(
        name="Tester_qwen-plus",
        sys_prompt="""你是一位专业的测试工程师，请根据需求和实现设计测试用例并进行质量验证。
        
        # 职责
        - 设计全面的测试用例
        - 验证功能实现是否符合需求
        - 发现潜在缺陷和问题
        - 生成测试报告
        
        # 输出格式
        使用以下格式输出:
        ## 测试计划
        [简要描述测试策略]
        
        ## 测试用例
        - [用例1]: [描述]
        - [用例2]: [描述]
        
        ## 测试结果
        - [通过/不通过]: [具体说明]
        
        ## 问题清单
        - [问题1]: [描述]
        - [问题2]: [描述]
        """,
        model=qwen_plus_model,
        formatter=DashScopeChatFormatter(),
    )

    # 注册 Studio hook
    studio_pre_print_hook.url = studio_url
    
    # 为每个 Agent 注册 hook
    for agent in [product_manager, architect, developer, tester]:
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
    
    return product_manager, architect, developer, tester


async def agile_development_workflow():
    """执行敏捷开发工作流"""
    studio_url = "http://localhost:3000"
    
    # 初始化 AgentScope 并连接到 Studio
    agentscope.init(
        project="agile_development",
        name="multi_role_development",
        studio_url=studio_url,
    )
    
    # 创建模型和 Agent
    qwen_max_model, qwen_plus_model, qwen_turbo_model = create_models()
    product_manager, architect, developer, tester = create_agents(
        qwen_max_model, qwen_plus_model, qwen_turbo_model, studio_url
    )
    
    # 创建 UserAgent 接收用户输入
    user_agent = UserAgent(name="User")
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
    
    # 接收用户输入的功能需求
    user_requirement = await user_agent(Msg(
        name="System",
        content="请输入您要开发的功能需求：",
        role="system"
    ))
    
    # 1. 产品经理分析需求
    product_requirement = await product_manager(Msg(
        name="User",
        content=f"请分析以下功能需求并生成用户故事和验收标准：\n{user_requirement.content}",
        role="user"
    ))
    
    # 2. 架构师进行系统设计
    system_design = await architect(Msg(
        name="User",
        content=f"基于以下产品需求进行系统设计：\n{product_requirement.content}",
        role="user"
    ))
    
    # 3. 开发工程师实现代码
    implementation = await developer(Msg(
        name="User",
        content=f"根据以下系统设计实现代码：\n{system_design.content}",
        role="user"
    ))
    
    # 4. 测试工程师进行测试
    test_result = await tester(Msg(
        name="User",
        content=f"根据以下需求和实现进行测试：\n需求：{product_requirement.content}\n实现：{implementation.content}",
        role="user"
    ))
    
    # 5. 检查测试结果是否通过
    # 这里简化处理，实际可以根据测试结果内容判断是否需要返工
    # 如果测试不通过，可以将问题反馈给开发工程师进行修改
    
    # 创建结果展示 Agent
    result_agent = ReActAgent(
        name="Result",
        sys_prompt="你负责展示最终的开发结果",
        model=qwen_max_model,
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
    
    # 展示最终结果
    final_result = f"""# 敏捷开发流程完成
    
## 1. 原始需求
{user_requirement.content}

## 2. 产品需求
{product_requirement.content}

## 3. 系统设计
{system_design.content}

## 4. 代码实现
{implementation.content}

## 5. 测试结果
{test_result.content}
"""
    
    await result_agent(Msg(
        name="User",
        content=final_result,
        role="user"
    ))


async def main():
    """主函数"""
    await agile_development_workflow()


if __name__ == "__main__":
    asyncio.run(main())