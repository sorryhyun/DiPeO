You should use tools as much as possible, ideally more than 50 times. You should also implement your own tests first before attempting the problem.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this DiPeO repository.

## Project Overview

DiPeO is a monorepo for building and executing AI-powered agent workflows through visual programming:
- **Frontend** (apps/web/): React-based visual diagram editor
- **Backend** (apps/server/): FastAPI server with GraphQL API
- **CLI** (apps/server/src/dipeo_server/cli/): Command-line tool for running diagrams (`dipeo` command)

## 📚 Documentation Structure

### Core Documentation
- **[Documentation Index](docs/index.md)** - Complete documentation overview
- **[User Guide](docs/README.md)** - Getting started with DiPeO
- **[Motivations](docs/motivations.md)** - Project background and philosophy

### Architecture & Design
- **[Overall Architecture](docs/architecture/overall_architecture.md)** - System architecture and tech stack
- **[GraphQL Layer](docs/architecture/graphql-layer.md)** - Complete GraphQL implementation (3-tier)
- **[Memory System Design](docs/architecture/memory_system_design.md)** - Conversation memory architecture
- **[GraphQL Subscriptions](docs/architecture/graphql-subscriptions.md)** - Real-time updates
- **[Diagram Execution](docs/architecture/diagram-execution.md)** - Execution engine details

### Diagram Formats
- **[Diagram Formats Overview](docs/formats/diagram_formats.md)** - Native, Light, Readable formats
- **[Light Diagram Guide](docs/formats/comprehensive_light_diagram_guide.md)** - Complete Light YAML guide ⭐
  - **Essential reading** for working with Light format diagrams
  - Includes syntax, examples, best practices

### Project Guides
- **[Code Generation Guide](docs/projects/code-generation-guide.md)** - Complete codegen pipeline
- **[DiPeOCC Guide](docs/projects/dipeocc-guide.md)** - Claude Code session conversion ⭐
- **[DiPeO AI Generation](docs/projects/dipeodipeo-guide.md)** - Natural language to diagrams
- **[Frontend Auto](projects/frontend_auto/README.md)** - Rapid AI-powered frontend generation
- **[Frontend Enhance](docs/projects/frontend-enhance-guide.md)** - Advanced intelligent memory selection

### Integrations
- **[Claude Code Integration](docs/integrations/claude-code.md)** - Claude Code SDK integration
- **[Webhook Integration](docs/features/webhook-integration.md)** - Webhook support

### Node Types
- **[Diff Patch Node](docs/nodes/diff-patch.md)** - File modification via diffs

## Essential Commands

### Setup & Development
```bash
make install          # Install all dependencies (installs uv if needed)
make dev-all          # Start both frontend and backend
make dev-server       # Start backend only
make dev-web          # Start frontend only
```

### Running Diagrams
```bash
# Run with debug mode (auto-starts monitoring server)
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=30

# Run with custom input data
dipeo run [diagram] --input-data '{"key": "value"}' --light --debug
```
- **Light diagrams**: Read [Light Diagram Guide](docs/formats/comprehensive_light_diagram_guide.md)
- **Debug mode (`--debug`)**: Automatically starts background server for real-time monitoring
- **Monitor executions**: Open `http://localhost:3000/?monitor=true` in browser when using `--debug`
- Use `simple_iter_cc` diagram to test Claude Code adapter

### Natural Language to Diagram
```bash
dipeo ask --to "create a workflow that fetches weather and sends email" --and-run
```
- See [DiPeO AI Generation Guide](docs/projects/dipeodipeo-guide.md)

### Converting Claude Code Sessions
```bash
dipeocc list                    # List recent Claude Code sessions
dipeocc convert --latest        # Convert latest session to diagram
dipeocc convert session-id      # Convert specific session
dipeocc watch --auto-execute    # Watch and auto-execute new sessions
dipeocc stats session-id        # Show session statistics
```
- **Session location**: `~/.claude/projects/-home-soryhyun-DiPeO/`
- **Output**: `projects/claude_code/sessions/{session_id}/`
- **Full guide**: [DiPeOCC Guide](docs/projects/dipeocc-guide.md)

### Integrations & API Management
```bash
dipeo integrations init               # Initialize integrations workspace
dipeo integrations validate            # Validate provider manifests
dipeo integrations openapi-import spec.yaml --name my-api
dipeo integrations claude-code --sync-mode auto --watch-todos
```

## Code Generation

**⚠️ WARNING**: Code generation overwrites ALL generated code in `dipeo/diagram_generated/`!

### Workflow
1. Modify TypeScript specs in `/dipeo/models/src/` → `cd dipeo/models && pnpm build`
2. Generate: `make codegen` (outputs to `dipeo/diagram_generated_staged/`)
3. Verify: `make diff-staged`
4. Apply: `make apply-test` (recommended) or `make apply` or `make apply-syntax-only`
5. Update GraphQL: `make graphql-schema`

Quick command: `make codegen-auto` (USE WITH CAUTION)

**Full guide**: [Code Generation Guide](docs/projects/code-generation-guide.md)

## GraphQL Operations System

### 3-Tier Architecture
1. **Generated Layer**: `/dipeo/diagram_generated/graphql/` (operations.py, inputs/results/types)
2. **Application Layer**: `/dipeo/application/graphql/` (direct service access resolvers)
3. **Execution Layer**: OperationExecutor with auto-discovery and validation

**45 operations** (23 queries, 21 mutations, 1 subscription) - Frontend hooks in `@/__generated__/graphql`, Python classes in `dipeo/diagram_generated/graphql/operations.py`

**Resolver Pattern**: Direct service access via `async def resolver(registry, **kwargs)` - no class-based resolvers except ProviderResolver

### Adding New GraphQL Operations
1. Add definition to `/dipeo/models/src/frontend/query-definitions/[entity].ts`
2. Build models: `cd dipeo/models && pnpm build`
3. Generate: `make codegen`
4. Apply: `make apply-test`
5. Update schema: `make graphql-schema`

**Full docs**: [GraphQL Layer Architecture](docs/architecture/graphql-layer.md)

## Quality Commands
```bash
make lint-server        # Lint Python
make lint-web           # Lint TypeScript
make format             # Format Python with ruff
pnpm typecheck          # TypeScript type checking
make graphql-schema     # Update GraphQL types
```

## Architecture Overview

### Key Concepts
- **Code Generation**: All models/schemas generated from TypeScript specs in `/dipeo/models/src/`
- **Generated Code**: Lives in `dipeo/diagram_generated/` (DO NOT EDIT DIRECTLY)
- **Diagrams**: Stored in `/examples/`, `/projects/`, or `/files/`
- **Service Architecture**: Mixin-based composition (LoggingMixin, ValidationMixin, ConfigurationMixin, CachingMixin, InitializationMixin)
- **Event System**: Unified EventBus protocol for all event handling
- **Output Pattern**: Envelope pattern with EnvelopeFactory for all handler outputs

### Key Architecture Documentation
- **[Overall Architecture](docs/architecture/overall_architecture.md)** - Complete system design
- **[Memory System](docs/architecture/memory_system_design.md)** - Conversation memory management
- **[Diagram Execution](docs/architecture/diagram-execution.md)** - Execution flow details
- **[GraphQL Layer](docs/architecture/graphql-layer.md)** - GraphQL implementation

### Node Handlers & IR Builders
- **Node Handlers**: `/dipeo/application/execution/handlers/` - api_job, db, diff_patch, endpoint, hook, integrated_api, person_job/, sub_diagram/, code_job/, condition/, codegen/
- **IR Builders**: `/dipeo/infrastructure/codegen/ir_builders/` - backend_builders, frontend, strawberry_builders

See [Overall Architecture](docs/architecture/overall_architecture.md) for details.

### Key Directories
- `/apps/server/` - FastAPI backend (includes CLI at src/dipeo_server/cli/)
- `/apps/web/` - React frontend ([Frontend README](apps/web/src/domain/README.md))
- `/dipeo/` - Backend business logic (application/domain/infrastructure layers)
- `/projects/codegen/` - Code generation system ([Codegen Guide](docs/projects/code-generation-guide.md))
- `/projects/frontend_auto/` - AI frontend generation ([Frontend Auto](projects/frontend_auto/README.md))
- `/projects/frontend_enhance/` - Advanced frontend generation ([Frontend Enhance](docs/projects/frontend-enhance-guide.md))

### LLM Infrastructure
- **Unified Client Architecture**: All providers use unified clients directly
- **OpenAI API v2**:
  - Uses `responses.create()` and `responses.parse()` APIs
  - `input` parameter for messages
  - `max_output_tokens` for token limits
  - Response structure: `response.output[0].content[0].text`
- **Domain Adapters**:
  - `LLMMemorySelectionAdapter`: Intelligent memory filtering and selection
  - `LLMDecisionAdapter`: Binary decision making for conditions
- **Provider Support**: OpenAI, Anthropic, Google, Ollama, Claude Code
- **Documentation**: [Claude Code Integration](docs/integrations/claude-code.md)

## Enhanced Service Registry

DiPeO uses **EnhancedServiceRegistry** for advanced dependency injection with production safety:
- **Service Types**: CORE, APPLICATION, DOMAIN, ADAPTER, REPOSITORY
- **Production Safety**: Registry freezing, final services (EVENT_BUS), immutable services (STATE_STORE)
- **Audit Trail**: Registration history, dependency validation, usage metrics

```python
from dipeo.infrastructure.enhanced_service_registry import EnhancedServiceRegistry, ServiceType

registry.register("my_service", instance, ServiceType.APPLICATION)
registry.register("critical", service, ServiceType.CORE, final=True)
history = registry.get_audit_trail()
```

Protected services: EVENT_BUS (final), STATE_STORE (immutable). Integrates with service mixins and EventBus.

## Claude Code Subagents

DiPeO includes specialized subagents in `.claude/agents/` for complex tasks:

- **dipeo-core-python**: Python business logic, handlers, infrastructure (`/dipeo/`)
- **dipeo-frontend-dev**: React components, ReactFlow editor, GraphQL hooks (`/apps/web/`)
- **typescript-model-designer**: TypeScript specs, node definitions (`/dipeo/models/src/`)
- **dipeo-codegen-specialist**: Code generation pipeline, IR builders, staging validation
- **dipeocc-converter**: Claude Code session conversion, DiPeOCC workflows
- **docs-maintainer**: Documentation updates after features/refactors
- **todo-manager**: Task planning, TODO.md management

Use these agents for specialized work requiring deep domain expertise.

## Adding New Features

### New Node Types
1. Create specification in `/dipeo/models/src/node-specs/`
2. Build models: `cd dipeo/models && pnpm build`
3. Generate: `make codegen`
4. Apply: `make apply-test`
5. Update GraphQL: `make graphql-schema`
6. See: [Code Generation Guide](docs/projects/code-generation-guide.md)

### Other Changes
- **API changes**: Modify GraphQL schema, then `make graphql-schema`
- **UI changes**: Work in `/apps/web/src/`
- **Documentation**: [GraphQL Layer](docs/architecture/graphql-layer.md)

## Important Notes

- **Python 3.13+** required
- Use **uv** for Python, **pnpm** for JavaScript (not npm/yarn)
- Default LLM: `gpt-5-nano-2025-08-07`
- Backend port: 8000, Frontend port: 3000
- **Service Architecture**: Services use mixin composition with unified EventBus and Envelope pattern
- **Enhanced Service Registry**: Production-ready dependency injection with type categorization, audit trails, and safety features

## Common Issues & Solutions

| Issue | Solution | Documentation |
|-------|----------|---------------|
| Import errors | Run `make install` (uv manages activation automatically) | |
| uv not found | `make install` (auto-installs uv) | |
| Generated code out of sync | Run codegen workflow (see above) | [Codegen Guide](docs/projects/code-generation-guide.md) |
| TypeScript errors | `make graphql-schema` | |
| Need debugging | Add `--debug` flag, check `.logs/` | |
| OpenAI API usage | Use `input` parameter and `max_output_tokens` | |
| Claude Code sessions | Use `dipeocc` to convert sessions | [DiPeOCC Guide](docs/projects/dipeocc-guide.md) |

## Testing & Debugging

- **Debug diagrams**: `dipeo run [diagram] --debug`
- **Monitor UI**: `http://localhost:3000/?monitor=true`
- **GraphQL playground**: `http://localhost:8000/graphql`
- **Logs**: Check `.logs/cli.log` for detailed debugging
- **Note**: Formal test suite is under development
