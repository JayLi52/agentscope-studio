# AgentScope Studio 狼人杀智能体设计

## 概述

AgentScope Studio 中的狼人杀游戏实现展示了一个基于角色的多智能体系统，具有结构化通信和决策机制。它为 9 名玩家设计，包含经典的狼人杀游戏角色。

## 核心组件

```
werewolves/
├── game.py            # 主游戏逻辑和流程控制
├── main.py            # 入口点和智能体初始化
├── prompt.py          # 角色特定提示词（中英文）
├── structured_model.py # Pydantic 结构化输出模型
├── utils.py           # 工具函数
└── README.md          # 文档
```

## 关键设计概念

### 1. 角色系统

| 角色         | 数量 | 能力说明                                                                 |
|--------------|------|--------------------------------------------------------------------------|
| 狼人         | 3    | 每晚杀死一名玩家；白天隐藏身份                                           |
| 村民         | 3    | 普通玩家无特殊能力；通过投票找出并淘汰狼人                               |
| 预言家       | 1    | 每晚可查验一名玩家的身份                                                 |
| 女巫         | 1    | 拥有两瓶一次性药水：解药（拯救一名夜间被杀死的玩家）+ 毒药（杀死一名玩家） |
| 猎人         | 1    | 被淘汰时可开枪带走一名玩家                                               |

### 2. 游戏流程

```
1. 角色分配（随机）
2. 夜间阶段：
   - 狼人选择受害者
   - 预言家查验身份
   - 女巫使用药水
3. 白天阶段：
   - 法官宣布夜间结果
   - 玩家讨论
   - 投票淘汰玩家
4. 检查胜利条件
```

### 3. 智能体设计

智能体使用 `ReActAgent` 实现，包含角色特定的系统提示词和结构化输出模型：

```python
class ReActAgent:
    - name: 玩家标识符
    - sys_prompt: 角色特定的规则和说明
    - model: LLM 后端（如 Qwen）
    - formatter: 模型特定的输出格式化器
```

### 4. 结构化输出

所有智能体决策都使用 Pydantic 模型，确保输出有效且可解析：

```python
# 结构化模型示例
class DiscussionModel(BaseModel):
    reach_agreement: bool  # 是否达成共识

class VoteModel(BaseModel):
    vote: Literal["Player1", "Player2", ...]  # 投票目标

class WitchPoisonModel(BaseModel):
    poison: bool  # 是否使用毒药
    name: Optional[Literal["Player1", ...]]  # 下毒目标
```

### 5. 通信管道

游戏使用 AgentScope 的管道模块管理交互：

```python
- MsgHub: 中央消息枢纽，用于广播消息
- sequential_pipeline: 按顺序处理智能体
- fanout_pipeline: 同时向多个智能体发送消息
- moderator: EchoAgent，用于格式化和转发消息
```

### 6. 会话管理

```python
# 支持连续游戏
session = JSONSession(save_dir="./checkpoints")
await session.load_session_state(
    session_id="players_checkpoint",
    **{player.name: player for player in players}
)
```

## 运行游戏

```bash
# 基本运行
python main.py

# 在 AgentScope Studio 中可视化运行
python main.py  # 确保 Studio 运行在 http://localhost:3000
```

## 自定义

1. **切换语言**：
   ```python
   # 默认中文
   from prompt import ChinesePrompts as Prompts

   # 英文
   # from prompt import EnglishPrompts as Prompts
   ```

2. **更换 LLM**：
   ```python
   # 相应更改 model_name 和 formatter
   model=DashScopeChatModel(
       api_key=os.environ.get("DASHSCOPE_API_KEY"),
       model_name="qwen3-max",
   ),
   formatter=DashScopeMultiAgentFormatter(),
   ```

3. **添加用户智能体**：
   ```python
   from agentscope.agent import UserAgent
   players[0] = UserAgent(name="我的用户")  # 用用户替换 Player1
   ```

## 技术栈

- **智能体框架**：AgentScope
- **LLM 后端**：Qwen (DashScope API)
- **结构化输出**：Pydantic
- **格式化器**：DashScopeMultiAgentFormatter
- **持久化**：JSONSession

该设计为基于角色的多智能体游戏提供了坚实的基础，具有清晰的通信协议和结构化决策机制。
