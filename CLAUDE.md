# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this DiPeO repository.

## Project Overview

DiPeO is a monorepo for building and executing AI-powered agent workflows through visual programming:
- **Frontend** (apps/web/): React-based visual diagram editor
- **Backend** (apps/server/): FastAPI server with GraphQL API  
- **CLI** (apps/cli/): Command-line tool for running diagrams (`dipeo` command)
- documents overall @docs/index.md

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
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=30
dipeo run [diagram] --input-data '{"key": "value"}' --light --debug
```
- **Light diagrams**: When working with light format diagrams, read `docs/formats/comprehensive_light_diagram_guide.md` for detailed documentation
- Add `--debug` for detailed logs
- use `simple_iter_cc` diagram for test claude code adapter
- Monitor at `http://localhost:3000/?monitor=true`

## Code Generation

**⚠️ WARNING**: Code generation overwrites ALL generated code in `dipeo/diagram_generated/`!

### Workflow
1. **Modify TypeScript specs** in `/dipeo/models/src/`, then: `cd dipeo/models && pnpm build`
2. **Generate**: `make codegen` (includes parse-typescript automatically)
3. **Verify**: `make diff-staged` to review changes
4. **Apply**: `make apply-syntax-only` (fast) or `make apply` (with type checking)
5. **Update GraphQL**: `make graphql-schema`

Quick command: `make codegen-auto` (runs all steps - USE WITH CAUTION)

### Staging System
- **Generated to**: `dipeo/diagram_generated_staged/` (for review - temporary staging area)
- **Active code**: `dipeo/diagram_generated/` (in use - DO NOT EDIT DIRECTLY)
- **Apply changes**: `make apply` moves staged → active after validation
- **Why staging**: Safety, validation, easy rollback
- **Full docs**: [Code Generation Guide](docs/projects/code-generation-guide.md)

## GraphQL Operations System

### 🎉 Implementation Status: COMPLETE
The GraphQL refactoring is **substantially complete** with a solid, production-ready architecture:
- ✅ **45 complete operations** with full GraphQL query strings as constants
- ✅ **Type-safe operation classes** with proper TypedDict for variables
- ✅ **Well-structured resolvers** following consistent patterns
- ✅ **Clean 3-tier architecture** separating concerns
- ✅ **ServiceRegistry integration** for dependency injection
- ✅ **No major refactoring needed** - architecture is solid and maintainable

### Architecture Overview (3-Tier System)
1. **Generated Layer** (`/dipeo/diagram_generated/graphql/`)
   - `operations.py` - All 45 operations with full support
   - `inputs.py`, `results.py`, `domain_types.py`, `enums.py` - Generated types
   
2. **Application Layer** (`/dipeo/application/graphql/`)
   - `schema/mutations/` - Organized by entity type
   - `schema/query_resolvers.py` - Standalone query resolvers
   - `operation_executor.py` - Central operation mapping

3. **Execution Layer** (Infrastructure)
   - EnhancedServiceRegistry for advanced dependency injection
   - Event-driven state management
   - Envelope system for type-safe data flow

### Adding New GraphQL Operations
1. **Add definition** to `/dipeo/models/src/frontend/query-definitions/[entity].ts`
2. **Build models**: `cd dipeo/models && pnpm build`
3. **Generate queries**: `make codegen`
4. **Apply changes**: `make apply-syntax-only`
5. **Update GraphQL schema**: `make graphql-schema`

### Query Definition Structure
```typescript
// In /dipeo/models/src/frontend/query-definitions/[entity].ts
export const entityQueries: EntityQueryDefinitions = {
  entity: 'EntityName',
  queries: [
    {
      name: 'GetEntity',
      type: QueryOperationType.QUERY,
      variables: [{ name: 'id', type: 'ID', required: true }],
      fields: [/* GraphQL fields */]
    }
  ]
}
```

### Generated Files & Operations
- **Frontend Queries**: `/apps/web/src/__generated__/queries/all-queries.ts` - All GraphQL operations
- **React Hooks**: `/apps/web/src/__generated__/graphql.tsx` - Type-safe hooks for each operation
- **Python Operations**: `/dipeo/diagram_generated/graphql/operations.py` - Typed Python classes
- **45 operations** currently defined (23 queries, 21 mutations, 1 subscription)

### Usage in Frontend
```typescript
// Import generated hooks
import { useGetExecutionQuery } from '@/__generated__/graphql';

// Use in components
const { data, loading } = useGetExecutionQuery({
  variables: { id: executionId }
});
```

### Usage in Python

```python
# Import generated operations
from dipeo.diagram_generated.graphql_backups.operations import (
    ExecuteDiagramOperation,
    GetExecutionOperation,
    EXECUTE_DIAGRAM_MUTATION
)

# Use query strings directly
query = EXECUTE_DIAGRAM_MUTATION

# Or use typed operation classes
variables = ExecuteDiagramOperation.get_variables_dict(
    input={"diagram_id": "example", "variables": {}}
)
```

### Key Benefits of Current Implementation
- **Type Safety**: Full type safety from TypeScript to Python
- **Consistency**: All resolvers follow established patterns
- **Maintainability**: Clean separation of concerns
- **Performance**: Optimized with per-execution caching
- **Developer Experience**: Auto-completion and inline documentation

For detailed architecture documentation, see [GraphQL Layer Architecture](docs/architecture/graphql-layer.md)

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

### Node Handlers - Path Reference
**Base Directory**: `/dipeo/application/execution/handlers/`

#### Individual Node Handlers (Direct Files)
- `api_job.py` - API call handling
- `db.py` - Database operations
- `endpoint.py` - HTTP endpoint handling
- `hook.py` - Hook/callback handling
- `integrated_api.py` - Integrated API operations
- `json_schema_validator.py` - JSON schema validation
- `start.py` - Start node handling
- `template_job.py` - Template processing
- `typescript_ast.py` - TypeScript AST operations
- `user_response.py` - User response handling

#### Complex Node Handlers (Subdirectories)
- **person_job/** - LLM/AI agent handling
  - `batch_executor.py` - Batch person execution
  - `conversation_handler.py` - Conversation management
  - `prompt_resolver.py` - Prompt resolution
  - `text_format_handler.py` - Text formatting
- **sub_diagram/** - Sub-diagram execution
  - `lightweight_executor.py` - Light diagram execution
  - `single_executor.py` - Single sub-diagram execution
  - `batch_executor.py` - Batch sub-diagram execution
  - `parallel_executor.py` - Parallel execution
  - `base_executor.py` - Base executor logic
- **code_job/** - Code execution
  - `executors/` - Various code executors
- **condition/** - Conditional logic
  - `evaluators/` - Condition evaluators

### Key Directories
- `/apps/server/` - FastAPI backend
- `/apps/web/` - React frontend
- `/apps/cli/` - CLI tool
- `/dipeo/` - Backend business logic (application/domain/infrastructure layers)
- `/projects/codegen/` - Code generation system

### LLM Infrastructure (Updated 2025)
- **Unified Client Architecture**: All providers use unified clients directly (no adapter/client separation)
- **OpenAI API v2 Migration**:
  - Uses new `responses.create()` and `responses.parse()` APIs
  - `messages` → `input` parameter
  - `max_tokens` → `max_output_tokens`
  - Temperature parameter no longer supported
  - Response structure: `response.output[0].content[0].text`
- **Domain Adapters**:
  - `LLMMemorySelectionAdapter`: Intelligent memory filtering and selection
  - `LLMDecisionAdapter`: Binary decision making for conditions
- **Provider Support**: OpenAI, Anthropic, Google, Ollama, Claude Code

## Enhanced Service Registry

### Overview
DiPeO uses an **EnhancedServiceRegistry** for advanced dependency injection with production safety features and comprehensive service management. This replaces the basic ServiceRegistry with enhanced capabilities for enterprise-grade service orchestration.

### Key Features

#### Service Type Categorization
All services are categorized by type for better organization and validation:
- **CORE**: Essential system services (EVENT_BUS, STATE_STORE)
- **APPLICATION**: Application-layer services (handlers, executors)
- **DOMAIN**: Domain logic services (business rules, validators)
- **ADAPTER**: External integrations (LLM clients, databases)
- **REPOSITORY**: Data access services (persistence layers)

#### Production Safety
- **Registry Freezing**: Automatically freezes in production after bootstrap to prevent accidental modifications
- **Final Services**: Critical services marked as final cannot be overridden (EVENT_BUS)
- **Immutable Services**: Core services marked as immutable cannot be modified (STATE_STORE)
- **Environment Detection**: Automatically detects production environment and applies safety constraints

#### Audit Trail & Debugging
- **Registration History**: Complete audit trail of all service registrations with timestamps
- **Dependency Validation**: Validates service dependencies and detects circular references
- **Usage Metrics**: Tracks service retrieval patterns for performance optimization
- **Service Health**: Monitors service lifecycle and availability

### Usage Examples

#### Basic Service Registration
```python
from dipeo.infrastructure.enhanced_service_registry import EnhancedServiceRegistry, ServiceType

registry = EnhancedServiceRegistry()

# Register with type categorization
registry.register("my_service", my_service_instance, ServiceType.APPLICATION)

# Register with special markers
registry.register("critical_service", service, ServiceType.CORE, final=True)
registry.register("config_service", config, ServiceType.DOMAIN, immutable=True)
```

#### Audit Trail Access
```python
# Get registration history for debugging
history = registry.get_audit_trail()
for entry in history:
    print(f"{entry.timestamp}: {entry.action} - {entry.service_name} ({entry.service_type})")

# Get service usage metrics
metrics = registry.get_service_metrics("EVENT_BUS")
print(f"Retrieved {metrics.retrieval_count} times")
```

#### Service Validation
```python
# Validate all dependencies before production deployment
validation_result = registry.validate_dependencies()
if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Dependency error: {error}")

# Check if registry is properly configured
if registry.is_frozen:
    print("Registry is production-ready and frozen")
```

#### Protected Services
```python
# Critical services are automatically protected
registry.get("EVENT_BUS")    # Always available, final service
registry.get("STATE_STORE")  # Always available, immutable service

# These services cannot be modified in production:
# - EVENT_BUS (final): Cannot be overridden
# - STATE_STORE (immutable): Cannot be modified
```

### Integration with Existing Architecture
- **Mixin Compatibility**: Works seamlessly with existing service mixins
- **EventBus Integration**: EVENT_BUS service is automatically protected as final
- **StateStore Protection**: STATE_STORE marked as immutable for data integrity
- **GraphQL Layer**: Integrates with GraphQL resolvers for dependency injection

### Best Practices
1. **Use Type Categories**: Always specify ServiceType when registering services
2. **Mark Critical Services**: Use `final=True` for services that should never be overridden
3. **Protect Core State**: Use `immutable=True` for configuration and state services
4. **Monitor in Development**: Use audit trail to debug service dependency issues
5. **Validate Before Production**: Always run dependency validation before deployment

### Migration from Basic ServiceRegistry
The migration is automatic - existing code continues to work with enhanced features available:
```python
# Old code still works
registry.register("service", instance)
service = registry.get("service")

# Enhanced features available
registry.register("service", instance, ServiceType.APPLICATION, final=True)
history = registry.get_audit_trail()
```

## Adding New Features

### New Node Types
1. Create specification in `/dipeo/models/src/node-specs/`
2. Build models: `cd dipeo/models && pnpm build`
3. Generate: `make codegen`
4. Apply: `make apply-syntax-only`
5. Update GraphQL: `make graphql-schema`

### Other Changes
- **API changes**: Modify GraphQL schema, then `make graphql-schema`
- **UI changes**: Work in `/apps/web/src/`

## Important Notes

- **Python 3.13+** required
- Use **uv** for Python, **pnpm** for JavaScript (not npm/yarn)
- Default LLM: `gpt-5-nano-2025-08-07`
- Backend port: 8000, Frontend port: 3000
- **v1.0 Refactoring Complete**: Services use mixin composition, unified EventBus, complete Envelope migration
- **Enhanced Service Registry**: Production-ready dependency injection with type categorization, audit trails, and safety features

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Run `make install` (uv manages activation automatically) |
| uv not found | `make install` (auto-installs uv) |
| Generated code out of sync | Run codegen workflow (see above) |
| TypeScript errors | `make graphql-schema` |
| Need debugging | Add `--debug` flag, check `.logs/` |
| OpenAI temperature error | Temperature not supported in new API, remove parameter |
| OpenAI max_tokens error | Use `max_output_tokens` instead of `max_tokens` |
| TokenUsage missing 'total' | Use `total_tokens` property instead |

## Testing & Debugging

- **Debug diagrams**: `dipeo run [diagram] --debug`
- **Monitor UI**: `http://localhost:3000/?monitor=true`
- **GraphQL playground**: `http://localhost:8000/graphql`
- **Logs**: Check `.logs/server.log` for detailed debugging
- **Note**: Formal test suite is under development
