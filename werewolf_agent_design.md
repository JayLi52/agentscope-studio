# Werewolf Agent Design in AgentScope Studio

## Overview

The werewolf game implementation in AgentScope Studio demonstrates a role-based multi-agent system with structured communication and decision-making. It's designed for 9 players with classic werewolf game roles.

## Core Components

```
werewolves/
├── game.py            # Main game logic and flow control
├── main.py            # Entry point and agent initialization
├── prompt.py          # Role-specific prompts (English/Chinese)
├── structured_model.py # Pydantic models for structured output
├── utils.py           # Utility functions
└── README.md          # Documentation
```

## Key Design Concepts

### 1. Role System

| Role         | Count | Abilities                                                                 |
|--------------|-------|---------------------------------------------------------------------------|
| Werewolf     | 3     | Kill one player each night; hide identity during the day                 |
| Villager     | 3     | Ordinary players; eliminate werewolves through voting                    |
| Seer         | 1     | Check one player's identity each night                                   |
| Witch        | 1     | Healing potion (save 1 player) + Poison potion (kill 1 player)           |
| Hunter       | 1     | Shoot one player when eliminated                                         |

### 2. Game Flow

```
1. Role Assignment (random)
2. Night Phase:
   - Werewolves choose victim
   - Seer checks identity
   - Witch uses potions
3. Day Phase:
   - Moderator announces night results
   - Discussion
   - Voting to eliminate player
4. Check win conditions
```

### 3. Agent Design

Agents are implemented using `ReActAgent` with role-specific system prompts and structured output models:

```python
class ReActAgent:
    - name: Player identifier
    - sys_prompt: Role-specific instructions and rules
    - model: LLM backend (e.g., Qwen)
    - formatter: Model-specific output formatter
```

### 4. Structured Output

All agent decisions use Pydantic models to ensure valid and parsable outputs:

```python
# Examples of structured models
class DiscussionModel(BaseModel):
    reach_agreement: bool

class VoteModel(BaseModel):
    vote: Literal["Player1", "Player2", ...]

class WitchPoisonModel(BaseModel):
    poison: bool
    name: Optional[Literal["Player1", ...]]
```

### 5. Communication Pipeline

The game uses AgentScope's pipeline module for managing interactions:

```python
- MsgHub: Central message hub for broadcasting
- sequential_pipeline: Process agents in order
- fanout_pipeline: Send message to multiple agents simultaneously
- moderator: EchoAgent to format and forward messages
```

### 6. Session Management

```python
# Support for continuous gaming
session = JSONSession(save_dir="./checkpoints")
await session.load_session_state(
    session_id="players_checkpoint",
    **{player.name: player for player in players}
)
```

## Running the Game

```bash
# Basic run
python main.py

# With visualization in AgentScope Studio
python main.py  # Ensure studio is running on http://localhost:3000
```

## Customization

1. **Change Language**:
   ```python
   # Chinese (default)
   from prompt import ChinesePrompts as Prompts

   # English
   # from prompt import EnglishPrompts as Prompts
   ```

2. **Replace LLM**:
   ```python
   # Change model_name and formatter accordingly
   model=DashScopeChatModel(
       api_key=os.environ.get("DASHSCOPE_API_KEY"),
       model_name="qwen3-max",
   ),
   formatter=DashScopeMultiAgentFormatter(),
   ```

3. **Add User Agent**:
   ```python
   from agentscope.agent import UserAgent
   players[0] = UserAgent(name="MyUser")  # Replace Player1 with user
   ```

## Technical Stack

- **Agent Framework**: AgentScope
- **LLM Backend**: Qwen (DashScope API)
- **Structured Output**: Pydantic
- **Formatting**: DashScopeMultiAgentFormatter
- **Persistence**: JSONSession

This design provides a solid foundation for role-based multi-agent games with clear communication protocols and structured decision-making.