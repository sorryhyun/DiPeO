# Application Layer

Orchestrates business logic between domain and infrastructure layers.

## Architecture
- **3-container DI**: Application → Infrastructure → Core
- **Event-driven**: Asynchronous communication via unified EventBus
- **Type-safe**: ServiceRegistry with compile-time guarantees
- **Mixin-based Services**: Optional composition with LoggingMixin, ValidationMixin, ConfigurationMixin, CachingMixin, InitializationMixin

## Directory Structure

### Bootstrap (`bootstrap/`)
- **application_container.py**: Main application container orchestration
- **infrastructure_container.py**: Infrastructure service initialization
- **containers.py**: Core container management and lifecycle
- **service_registry.py**: Type-safe service locator implementation
- **wiring.py**: Dependency injection wiring configuration
- **lifecycle.py**: Component lifecycle protocols
- **port_metrics.py**: Performance metrics tracking

### Execution Engine (`execution/`)
- **engine.py**: TypedExecutionEngine - event-driven node execution
- **orchestrators/**: Central coordination for execution concerns
  - Person management with unified caching
  - Prompt loading delegation
  - Memory selection via LLMMemorySelector
  - LLM decision execution
- **handlers/**: Node-specific execution handlers
  - Simple handlers: Single file (e.g., `start.py`, `api_job.py`, `db.py`)
  - Complex handlers: Package structure (e.g., `person_job/`, `code_job/`, `sub_diagram/`)
- **states/**: Execution state management
- **observers/**: Event observation and monitoring
- **use_cases/**: Business logic use cases

### GraphQL API (`graphql/`)
- **schema/**: GraphQL schema definitions
  - queries.py: Query resolvers
  - mutations/: Mutation implementations
  - subscriptions.py: Real-time subscriptions
- **resolvers/**: Business logic resolvers
- **types/**: GraphQL type definitions
- **schema_factory.py**: Schema assembly

### Conversation Management (`conversation/`)
- **wiring.py**: Conversation context dependency injection
- **use_cases/manage_conversation.py**: Conversation lifecycle management

### Diagram Operations (`diagram/`)
- **wiring.py**: Diagram service dependency injection
- **use_cases/**: Diagram-specific operations
  - compile_diagram.py: Diagram compilation logic
  - load_diagram.py: Loading from various sources
  - serialize_diagram.py: Format conversion
  - validate_diagram.py: Structure validation

### Registry (`registry/`)
- **service_registry.py**: Type-safe service locator
- **keys.py**: Service key definitions

### Utilities (`utils/`)
- **prompt_builder.py**: Dynamic prompt construction

## Service Registry
```python
# Type-safe service registration
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
registry.register(LLM_SERVICE, llm_service_instance)
llm_service = registry.resolve(LLM_SERVICE)  # Type-safe
```

## Event Architecture

- **AsyncEventBus**: Fire-and-forget event distribution
- **CacheFirstStateStore**: Cache-first persistence with Phase 4 optimizations
- **Benefits**: No global locks, true parallel execution, clean separation

## Execution Flow
1. Compile diagram (uses CompileTimeResolver for connections)
2. Auto-register handlers
3. Initialize event bus
4. Execute loop:
   - Calculate ready nodes (DomainDynamicOrderCalculator)
   - Resolve inputs (domain.execution.resolution.api.resolve_inputs)
   - Execute handlers
   - Emit events (async persistence)
5. Handle errors via events

## Node Handlers

```python
@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    async def execute_request(self, request: ExecutionRequest) -> Envelope:
        # Use orchestrator for person management
        person = await self.orchestrator.get_or_create_person(person_id)
        
        # Return output using EnvelopeFactory
        return EnvelopeFactory.create(
            body=result_data,
            produced_by=str(node.id),
            trace_id=request.execution_id
        )
```

- Auto-discovered via `@register_handler` decorator
- Receive: node instance, context, inputs, services
- Return Envelope objects using EnvelopeFactory
- Support single-file or package structure
- Use ExecutionOrchestrator for person/memory/prompt management

### Output Handling

All handlers use the **Envelope pattern**:

```python
# Text output
EnvelopeFactory.create(content, produced_by=node_id, trace_id=trace_id)

# JSON/object output  
EnvelopeFactory.create(data, produced_by=node_id, trace_id=trace_id)

# Binary output
EnvelopeFactory.create(bytes_data, produced_by=node_id, trace_id=trace_id)

# Error output
EnvelopeFactory.create(msg, error="Error", produced_by=node_id, trace_id=trace_id)

# With multiple representations
envelope = EnvelopeFactory.create(data, produced_by=node_id, trace_id=trace_id)
envelope = envelope.with_representations({
    "text": str(data),
    "object": data,
    "markdown": format_as_markdown(data)
})
```

Benefits:
- **Type safety**: Content-type aware transformations
- **Multiple representations**: Same data in different formats
- **Clean API**: Consistent interface across all handlers
- **Traceability**: Built-in trace_id and produced_by metadata

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

## Key Imports

```python
from dipeo.domain.execution.resolution import RuntimeInputResolver, TransformationEngine
from dipeo.domain.execution.envelope import EnvelopeFactory
from dipeo.domain.diagram.compilation import CompileTimeResolver, Connection
from dipeo.domain.events import EventType, ExecutionEvent
from dipeo.domain.ports.storage import FileSystemPort
from dipeo.domain.integrations.api_services import APIBusinessLogic
from dipeo.application.execution.orchestrators import ExecutionOrchestrator
from dipeo.application.execution.use_cases import PromptLoadingUseCase
```

## Diagram Access Patterns

### ✅ DO: Use diagram query methods
Always use ExecutableDiagram's built-in query methods for accessing diagram data:

```python
# Get a specific node
node = context.diagram.get_node(node_id)

# Get nodes by type
person_job_nodes = context.diagram.get_nodes_by_type(NodeType.PERSON_JOB)

# Get incoming edges for a node
incoming = context.diagram.get_incoming_edges(node_id)

# Get outgoing edges for a node
outgoing = context.diagram.get_outgoing_edges(node_id)

# Get start nodes
start_nodes = context.diagram.get_start_nodes()
```

### ❌ DON'T: Direct access to internals
Never directly access diagram internal collections:

```python
# BAD: Direct access to nodes
for node in diagram.nodes:  # ❌ Don't do this
    if node.type == NodeType.PERSON_JOB:
        ...

# GOOD: Use query method
for node in diagram.get_nodes_by_type(NodeType.PERSON_JOB):  # ✅ Do this
    ...

# BAD: Direct access to edges
incoming = [e for e in diagram.edges if e.target_node_id == node_id]  # ❌

# GOOD: Use query method
incoming = diagram.get_incoming_edges(node_id)  # ✅
```

### Why This Matters
- **Performance**: Query methods use pre-indexed lookups (O(1) instead of O(n))
- **Maintainability**: Internal structure can change without breaking code
- **Type Safety**: Query methods provide consistent interfaces
- **Testing**: Easier to mock query methods than complex diagram structures

### Enforcement
A pre-commit hook (`check-diagram-access.py`) enforces these patterns in the application layer.
