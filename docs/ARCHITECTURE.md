# DiPeO Architecture Overview

This document provides a high-level overview of DiPeO's architecture, focusing on the execution flow from diagram files to node execution.

## System Overview

DiPeO (Diagrammed People & Organizations) is a visual programming environment for building AI-powered agent workflows. The system follows a layered architecture with clear separation of concerns:

```
┌───────────────────────┐
│       Frontend (React)              │
│      Visual Diagram Editor                  │
└───────────┬────────────┘
                      │ GraphQL/WebSocket
┌─────────────────────▼───────────┐
│                    Backend (FastAPI)                         │
│              GraphQL API + WebSocket Support                 │
└───────────┬──────────────────────┘
                      │
┌───────────▼───────────────────┐
│                     Core Services                        │
│     (DiagramService, ExecutionService, LLMService, etc)  │
└────────────┬──────────────────┘
                        │
┌────────────▼─────────────┐
│           Execution Engine                    │
│     (UnifiedExecutor + Node Handlers)         │
└─────────────────────────┘
```

## Execution Flow

The following diagram shows the complete flow from diagram file to execution:

```
files/diagram.json
        │
        ▼
┌──────────┐
│   CLI/Frontend    │
│ (DiagramRunner)   │
└────┬─────┘
          │ HTTP/GraphQL
          ▼
┌───────────────────┐
│  FastAPI Route    │
│ (/graphql)        │
└─────────┬─────────┘
          │
          ▼
┌───────────┐
│ GraphQLContext    │
│ (Request wrapper) │
└────┬─────┘
          │
          ▼
┌──────────┐
│ ExecutionService  │
│ (Business logic)  │
└────┬─────┘
          │
          ▼
┌──────────┐
│ UnifiedExecutor   │
│ (Orchestration)   │
└────┬─────┘
          │
          ▼
┌──────────┐
│  Node Handlers    │
│ (Actual execution)│
└──────────┘
```

### Step-by-Step Flow

1. **Diagram Loading**: A diagram file (JSON/YAML) is loaded from `files/diagrams/`
   
2. **CLI/Frontend Request**: The CLI's `DiagramRunner` or the web frontend sends the diagram to the backend via GraphQL mutation

3. **FastAPI Route**: The `/graphql` endpoint receives the request and creates a GraphQLContext

4. **GraphQL Context**: Wraps the request with authentication and service access

5. **Execution Service**: 
   - Validates the diagram
   - Creates an execution record
   - Prepares the execution context
   - Initiates the execution process

6. **Unified Executor**:
   - Loads node handlers from the registry
   - Manages the execution graph
   - Handles node dependencies and parallel execution
   - Streams updates via WebSocket

7. **Node Handlers**:
   - Individual handlers for each node type (PersonJob, Endpoint, etc.)
   - Execute the actual business logic
   - Return results to the executor

## Key Components

### Services Layer

All services extend `BaseService` and are available through dependency injection:

- **DiagramService**: Manages diagram CRUD operations
- **ExecutionService**: Orchestrates diagram execution
- **LLMService**: Handles LLM integrations (OpenAI, Anthropic, etc.)
- **NotionService**: Integrates with Notion API
- **FileService**: Manages file operations
- **APIKeyService**: Handles API key management

### Execution Components

- **RuntimeCtx**: Runtime execution context containing:
  - Current execution state
  - Node outputs
  - API keys and configurations
  - Execution metadata

- **Node Handlers**: Pluggable handlers for each node type:
  - `PersonJobHandler`: Executes LLM-based agent tasks
  - `EndpointHandler`: Handles data output and file saving
  - `ConditionHandler`: Evaluates conditional logic
  - `NotionHandler`: Interacts with Notion databases
  - `DBHandler`: Database operations

### Data Flow

1. **Input Processing**: Nodes receive inputs from connected edges
2. **Execution**: Handlers process inputs using injected services
3. **Output Generation**: Results are stored in the execution context
4. **Result Propagation**: Outputs flow to downstream nodes via edges

## Domain Model Structure

The system uses TypeScript-first domain models that generate:

```
packages/domain-models/src/
        │ (TypeScript definitions)
        ▼
┌───────────────────┐
│ Code Generation                   │
└─────────┬─────────┘
                   │
                   ├──► Python Models (dipeo_domain)
                   ├──► GraphQL Schema
                   └──► CLI Argument Types
```

## WebSocket Communication

Real-time updates during execution:

```
Client ◄──── WebSocket ────► Server
  │                               │
  ├─ Subscribe to execution ───┤
  ├─ Node status updates ◄─────┤
  ├─ Progress notifications ◄──┤
  └─ Final results ◄───────────┘
```

## Error Handling

The system uses a hierarchical exception structure:

- `AgentDiagramException` (base)
  - `ValidationError`
  - `DiagramExecutionError`
  - `NodeExecutionError`
  - `LLMServiceError`
  - etc.

## Security Considerations

- API keys are stored securely and never exposed in responses
- GraphQL queries are validated against the schema
- File operations are sandboxed to specific directories
- LLM prompts are sanitized before execution

## Development Workflow

1. Define domain models in TypeScript
2. Run `make codegen` to generate Python models and GraphQL schema
3. Implement service logic extending `BaseService`
4. Create node handlers implementing the `NodeHandler` protocol
5. Register handlers in the executor
6. Add GraphQL resolvers for new operations
7. Update frontend to use new features

## Testing Strategy

- Unit tests for individual services
- Integration tests for execution flow
- GraphQL schema tests
- WebSocket connection tests
- End-to-end tests via CLI

## Deployment Considerations

- Frontend and backend can be deployed separately
- WebSocket support required for real-time updates
- Environment variables for configuration
- Docker support for containerized deployment