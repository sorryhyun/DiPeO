# DiPeO Server

The backend API server for DiPeO, providing GraphQL and REST endpoints for diagram execution and management.

## Architecture

```
apps/server/
├── src/dipeo_server/
│   ├── api/           # FastAPI/GraphQL adapters
│   ├── infra/         # Infrastructure (state storage, caching)
│   └── app_context.py # Container configuration
├── main.py            # Server entry point
├── main_bundled.py    # PyInstaller entry point
└── schema.graphql     # GraphQL schema
```

## Key Components

### API Layer (`api/`)
- **GraphQL Router**: Strawberry-based GraphQL with subscriptions
- **SSE Endpoints**: Direct streaming for real-time execution updates
- **Context Management**: Request-scoped dependency injection

### Infrastructure (`infra/`)
- **StateRegistry**: SQLite-based execution state persistence
- **ExecutionCache**: In-memory cache for active executions
- **MessageStore**: Conversation history storage

### Container System
Uses simplified 3-container architecture:
- **CoreContainer**: Domain services (validators, utilities)
- **InfrastructureContainer**: External adapters (storage, LLM)
- **ApplicationContainer**: Use cases and orchestration

## Running the Server

```bash
# Development
make dev-server              # Runs on port 8000

# Production (multi-worker)
WORKERS=4 python main.py     # Hypercorn with 4 workers

# Bundled executable
make build-server           # Creates standalone executable
./dist/dipeo-server         # Run bundled server
```

## GraphQL Endpoints

- **Playground**: http://localhost:8000/graphql
- **Queries**: Diagrams, executions, persons, API keys
- **Mutations**: CRUD operations, diagram execution
- **Subscriptions**: Real-time execution updates

## Environment Variables

- `PORT`: Server port (default: 8000)
- `WORKERS`: Number of worker processes (default: 4)
- `REDIS_URL`: Redis for multi-worker subscriptions (optional)
- `STATE_STORE_PATH`: SQLite database path
- `LOG_LEVEL`: Logging verbosity (INFO/DEBUG)

## SSE Streaming

Direct streaming endpoint for browser clients:
```
GET /sse/executions/{execution_id}
```

Provides real-time execution updates without WebSocket complexity.
