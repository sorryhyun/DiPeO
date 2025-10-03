# DiPeO Applications

This directory contains the three main DiPeO applications: server (backend), web (frontend), and CLI.

## Server (Backend API)

FastAPI server providing GraphQL and REST endpoints for diagram execution.

### Architecture
```
apps/server/
├── src/dipeo_server/
│   ├── api/           # FastAPI/GraphQL adapters
│   ├── infra/         # Infrastructure (state, caching)
│   └── app_context.py # Container configuration
├── main.py            # Entry point
└── schema.graphql     # GraphQL schema
```

### Key Features
- **GraphQL**: Strawberry-based with subscriptions at `/graphql`
- **SSE Streaming**: Real-time updates via `/sse/executions/{id}`
- **State Management**: SQLite persistence + in-memory cache
- **Multi-worker**: Hypercorn support with `WORKERS=4 python main.py`

### Environment Variables
- `PORT`: Server port (default: 8000)
- `WORKERS`: Worker processes (default: 4)
- `STATE_STORE_PATH`: SQLite database path
- `LOG_LEVEL`: INFO/DEBUG

## Web (Frontend)

React-based visual diagram editor - see [apps/web/CLAUDE.md](web/CLAUDE.md) for details.

## CLI

Command-line tool integrated into the server package at `apps/server/src/dipeo_server/cli/`.

### Key Components
- **Server Manager**: Automatic backend lifecycle management
- **Display System**: Rich terminal UI with GraphQL subscriptions
- **Commands**: run, ask, claude_code (dipeocc), integrations, convert, metrics

## Development Guidelines

See root [CLAUDE.md](/CLAUDE.md) for:
- Code generation workflow
- Package management (uv, pnpm)
- GraphQL development
- Testing & debugging
- Common issues
