# Application Layer Architecture

The application layer orchestrates business logic between domain and infrastructure layers, implementing DiPeO's event-driven execution architecture.

## Architectural Principles

- **3-container DI**: Application → Infrastructure → Core containers
- **Event-driven**: Asynchronous communication via unified EventBus
- **Type-safe**: ServiceRegistry with compile-time guarantees
- **Mixin-based Services**: Optional composition with LoggingMixin, ValidationMixin, ConfigurationMixin, CachingMixin, InitializationMixin

## Directory Structure

### Bootstrap (`bootstrap/`)
Dependency injection and container management:
- **application_container.py**: Main application container orchestration
- **infrastructure_container.py**: Infrastructure service initialization
- **containers.py**: Core container management and lifecycle
- **service_registry.py**: Type-safe service locator implementation
- **wiring.py**: Dependency injection wiring configuration
- **lifecycle.py**: Component lifecycle protocols
- **port_metrics.py**: Performance metrics tracking

### Execution Engine (`execution/`)
Core execution engine for diagram workflows:

**engine/** - Core components:
- **typed_engine.py**: TypedExecutionEngine - event-driven node execution
  - Configurable concurrency via `ENGINE_MAX_CONCURRENT` setting
- **scheduler.py**: NodeScheduler - optimized node scheduling
  - Pre-fetched edge maps for efficient ready-node detection
  - Eliminates N+1 query patterns
- **context.py**: TypedExecutionContext - execution context management
- **dependency_tracker.py**: DependencyTracker - node dependency tracking
- **ready_queue.py**: ReadyQueue - ready node queue management
- **node_executor.py**: execute_single_node - single node execution logic
- **request.py**: ExecutionRequest - execution request modeling
- **helpers.py**: Helper utilities (get_handler, extract_llm_usage, format_node_result)
- **reporting.py**: Reporting utilities (calculate_progress)
- Uses lazy imports via `__getattr__` to avoid circular dependencies

**orchestrators/** - Central coordination:
- Person management with unified caching
- Prompt loading delegation
- Memory selection via LLMMemorySelector
- LLM decision execution

**handlers/** - Node-specific execution:
- Simple handlers: Single file (e.g., `start.py`, `api_job.py`, `db.py`)
- Complex handlers: Package structure (e.g., `person_job/`, `code_job/`, `sub_diagram/`)
- Async I/O throughout (aiofiles for file operations)

**states/** - Execution state management
**observers/** - Event observation and monitoring
**use_cases/** - Business logic use cases

### GraphQL API (`graphql/`)
GraphQL schema and resolvers:
- **schema/**: GraphQL schema definitions
  - queries.py: Query resolvers
  - mutations/: Mutation implementations
  - subscriptions.py: Real-time subscriptions
- **resolvers/**: Business logic resolvers
- **types/**: GraphQL type definitions
- **schema_factory.py**: Schema assembly

### Diagram Operations (`diagram/`)
Diagram-specific operations:
- **wiring.py**: Diagram service dependency injection
- **use_cases/**: Diagram-specific operations
  - compile_diagram.py: Diagram compilation logic
  - load_diagram.py: Loading from various sources
  - serialize_diagram.py: Format conversion
  - validate_diagram.py: Structure validation

### Registry (`registry/`)
Type-safe service management:
- **service_registry.py**: Type-safe service locator
- **keys.py**: Service key definitions

## Service Registry Design

Type-safe service registration and resolution:

```python
# Type-safe service registration
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
registry.register(LLM_SERVICE, llm_service_instance)
llm_service = registry.resolve(LLM_SERVICE)  # Type-safe
```

## Event Architecture

- **AsyncEventBus**: Fire-and-forget event distribution
- **CacheFirstStateStore**: Cache-first persistence with optimized performance
- **Benefits**: No global locks, true parallel execution, clean separation

## Execution Flow

1. **Compile diagram** - Uses CompileTimeResolver for connections
2. **Auto-register handlers** - Handler discovery and registration
3. **Initialize event bus** - Set up event distribution
4. **Execute loop**:
   - Calculate ready nodes (DomainDynamicOrderCalculator)
   - Resolve inputs (domain.execution.resolution.api.resolve_inputs)
   - Execute handlers
   - Emit events (async persistence)
5. **Handle errors** - Via events

## Node Handlers Architecture

Handlers auto-discovered via `@register_handler` decorator:

**Input**:
- Node instance
- Context
- Inputs
- Services

**Output**:
- Envelope objects using EnvelopeFactory

**Structure**:
- Support single-file or package structure
- Use ExecutionOrchestrator for person/memory/prompt management

## Output Handling: Envelope Pattern

All handlers use the **Envelope pattern** for type-safe outputs:

**Benefits**:
- Type safety: Content-type aware transformations
- Multiple representations: Same data in different formats
- Clean API: Consistent interface across all handlers
- Traceability: Built-in trace_id and produced_by metadata

## Design Principles

1. **Separation of Concerns**: Domain (logic) ←→ Application (orchestration) ←→ Infrastructure (I/O)
2. **Dependency Injection**: Via ServiceRegistry
3. **Type Safety**: Compile-time guarantees
4. **Event-Driven**: Async, decoupled communication
5. **Extensibility**: Add handlers for new node types
6. **Single Source of Truth**: ExecutionOrchestrator for execution-time concerns
7. **Context-First**: Access execution context directly (e.g., `context.diagram`)

## Integration Points

**Domain Layer**:
- `dipeo.domain.diagram.compilation` - Compile-time resolution
- `dipeo.domain.execution.resolution` - Runtime input resolution
- `dipeo.domain.events` - Event contracts
- `dipeo.domain.ports.storage` - Storage interfaces

**Infrastructure Layer**:
- AsyncEventBus, CacheFirstStateStore, MessageRouter

**Server Layer**:
- GraphQL/REST adapters, event bus initialization

## Diagram Access Patterns

### Why This Matters
- **Performance**: Query methods use pre-indexed lookups (O(1) instead of O(n))
- **Maintainability**: Internal structure can change without breaking code
- **Type Safety**: Query methods provide consistent interfaces
- **Testing**: Easier to mock query methods than complex diagram structures

### Enforcement
A pre-commit hook (`check-diagram-access.py`) enforces these patterns in the application layer.
