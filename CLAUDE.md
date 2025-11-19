# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentScope Studio is a local visualization toolkit for agent application development, supporting project management, runtime visualization, tracing, and agent evaluation. It includes a built-in Copilot named Friday for development assistance.

## Repository Structure

```
agentscope-studio/
├── assets/             # Project assets and images
├── bin/               # CLI entry point
├── checkpoints/       # Checkpoint files
├── packages/          # Monorepo packages
│   ├── app/          # Python application code
│   │   ├── agile_development/  # Agile development workflow module
│   │   ├── friday/             # Friday Copilot implementation
│   │   ├── judging/            # Multi-model judging system
│   │   └── werewolves/         # Werewolf game agent demo
│   ├── client/       # Frontend client (React + TypeScript)
│   ├── server/       # Backend server (Express + TypeScript)
│   └── shared/       # Shared code between client and server
├── LICENSE
├── README.md
└── package.json
```

## Common Development Commands

```bash
# Install dependencies
npm install

# Run development server (client + server)
npm run dev

# Run only client
npm run dev:client

# Run only server
npm run dev:server

# Build the project
npm run build

# Format code
npm run format

# Run werewolf agent demo
cd packages/app/werewolves && python main.py
```

## Key Technologies

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Express + TypeScript + tRPC + Socket.io
- **Database**: SQLite3 + TypeORM
- **Monorepo**: npm workspaces

## Architecture Overview

1. **Client**: React-based UI for visualization and user interaction
2. **Server**: Backend API server that handles client requests and communication with AgentScope applications
3. **Shared**: Common types and utilities used by both client and server
4. **App**: Python modules for advanced features:
   - **agile_development**: Agile development workflow module
   - **friday**: Built-in Copilot implementation
   - **judging**: Multi-model parallel judging system
   - **werewolves**: Role-based multi-agent game demo

The client and server communicate via tRPC for API requests and Socket.io for real-time updates.

## QuickStart for Connecting AgentScope

```python
import agentscope

agentscope.init(
    # ... other configs
    studio_url="http://localhost:3000"
)
```

## Werewolf Agent Demo

The repository includes a 9-player werewolf game demo that showcases:
- Role-based multi-agent interactions
- Structured output handling using Pydantic
- Complex interaction management with MsgHub and pipelines

To run:
```bash
cd packages/app/werewolves && python main.py
```

The game features:
- 3 Werewolves, 3 Villagers, 1 Seer, 1 Witch, 1 Hunter
- Night and day phases with role-specific abilities
- Structured discussion and voting
- Session persistence for continuous gaming
