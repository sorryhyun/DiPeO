# DiPeO Applications

This directory contains the three main DiPeO applications: server (backend), web (frontend), and CLI.

## Quick Start

```bash
# Start both frontend and backend
make dev-all

# Or run individually
make dev-server   # Backend on port 8000
make dev-web      # Frontend on port 3000

# Use CLI
dipeo run examples/simple_diagrams/simple_iter --light --debug
```

## 1. Server (Backend API)

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

## 2. Web (Frontend)

React-based visual diagram editor built with XYFlow.

### Tech Stack
- **Core**: React 19 + TypeScript + Vite
- **Diagram**: XYFlow for visual editing
- **State**: Zustand with flattened store
- **GraphQL**: Apollo Client with generated hooks
- **UI**: TailwindCSS + React Hook Form + Zod

### Architecture
```
apps/web/src/
├── __generated__/      # GraphQL types (DO NOT EDIT)
├── domain/             # Business logic
│   ├── diagram/        # Diagram editing
│   └── execution/      # Execution monitoring
├── infrastructure/     # Technical services
│   ├── store/          # Zustand state
│   └── hooks/          # Cross-cutting hooks
└── ui/components/      # UI components
```

### Commands
```bash
pnpm dev         # Start dev server
pnpm build       # Production build
pnpm typecheck   # Type checking
pnpm codegen     # Generate GraphQL types
```

### Key Patterns
```typescript
// Domain hooks
import { useDiagramManager } from '@/domain/diagram';

// Generated GraphQL
import { useGetDiagramQuery } from '@/__generated__/graphql';

// State access
const store = useStore();
```

### URL Parameters
- `?diagram={format}/{filename}` - Load diagram
- `?monitor=true` - Monitor mode
- `?debug=true` - Debug mode

## 3. CLI

Command-line tool for running diagrams and managing DiPeO.

### Architecture
```
apps/cli/
├── src/dipeo_cli/
│   ├── commands/           # CLI command implementations
│   │   ├── run_command.py      # Diagram execution
│   │   ├── ask_command.py      # Natural language to diagram
│   │   ├── claude_code_command.py  # Claude Code integration (dipeocc)
│   │   ├── integrations_command.py # Integration management
│   │   ├── convert_command.py  # Format conversion utilities
│   │   ├── metrics_command.py  # Performance metrics
│   │   └── utils_command.py    # Utility commands
│   ├── display/            # Terminal UI components
│   │   ├── components.py       # Rich terminal components
│   │   ├── execution_display.py # Real-time execution display
│   │   ├── styles.py           # Terminal styling
│   │   └── subscription_client.py # GraphQL subscription client
│   ├── __main__.py         # Main CLI entry point
│   └── server_manager.py   # Backend server lifecycle management
├── README.md               # Detailed CLI documentation
└── pyproject.toml          # CLI package configuration
```

### Installation
```bash
make install-cli  # Install globally as 'dipeo' and 'dipeocc'
```

### Core Commands
```bash
# Run diagrams
dipeo run [diagram_path] --light --debug

# Natural language to diagram
dipeo ask --to "create workflow" --and-run

# Convert Claude Code sessions (dipeocc alias)
dipeocc list
dipeocc convert --latest
dipeocc watch --auto-execute

# Manage integrations
dipeo integrations init
dipeo integrations validate
dipeo integrations openapi-import

# Utilities
dipeo convert [format]  # Convert between diagram formats
dipeo metrics          # Show performance metrics
```

### Key Components

#### Server Manager
- Automatically starts/stops backend server when needed
- Manages server lifecycle for CLI operations
- Handles port conflicts and cleanup

#### Display System
- Rich terminal UI with progress bars and tables
- Real-time execution monitoring with GraphQL subscriptions
- Color-coded output for different node types
- Interactive components for user input nodes

#### Command Structure
- **run**: Execute diagrams with various options (--light, --debug, --timeout)
- **ask**: Natural language to diagram generation using LLMs
- **claude_code** (dipeocc): Convert Claude Code sessions to executable diagrams
- **integrations**: Manage API integrations and provider manifests
- **convert**: Transform between diagram formats (native/light/readable)
- **metrics**: Display execution performance and statistics

### Features
- Light YAML diagram support with hot reload
- Real-time execution monitoring with colored output
- Claude Code session conversion and watching
- Integration management with OpenAPI import
- Natural language diagram generation
- Automatic server management
- Rich terminal UI with progress tracking

## Development Guidelines

### Code Generation
- **Never edit generated files** (`__generated__/`, `diagram_generated/`)
- Modify TypeScript specs in `/dipeo/models/src/` instead
- Run `make codegen` to regenerate

### Package Management
- **Python**: Use `uv` (auto-managed)
- **JavaScript**: Use `pnpm` (not npm/yarn)

### State Management
- **Server**: EnhancedServiceRegistry with production safety
- **Web**: Zustand with factory patterns
- **CLI**: Stateless execution

### GraphQL Development
1. Define operations in `/dipeo/models/src/frontend/query-definitions/`
2. Build: `cd dipeo/models && pnpm build`
3. Generate: `make codegen && make apply`
4. Update schema: `make graphql-schema`

### Testing & Debugging
- Server logs: `.logs/server.log`
- GraphQL Playground: `http://localhost:8000/graphql`
- Add `--debug` flag to CLI commands
- Frontend debug: `?debug=true` URL parameter

## Important Notes

- **Python 3.13+** required for all Python apps
- **Type Safety**: Maintain strict typing in both TypeScript and Python
- **Generated Code**: All models/schemas generated from TypeScript specs
- **Service Architecture**: Uses mixin composition with unified EventBus
- **Production Safety**: EnhancedServiceRegistry with freezing and audit trails

## Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Run `make install` |
| TypeScript errors | `make graphql-schema` |
| Generated code out of sync | Full codegen workflow |
| Server not starting | Check port 8000 availability |
| Frontend build fails | `pnpm install` in web directory |
