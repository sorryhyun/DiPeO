# DiPeO Core Execution Module

## Overview

The `dipeo/core/execution` module provides the foundational execution engine for DiPeO's diagram-based workflow system. It manages runtime state, node output contracts, execution tracking, and dynamic node scheduling during diagram execution.

## Architecture

The execution module implements a **protocol-based architecture** with clear separation between:
- **Static Components**: Node output protocols and contracts
- **Dynamic Components**: Runtime state management and execution context
- **Orchestration**: Dynamic scheduling and execution tracking

### Key Design Patterns
- **Protocol Pattern**: Type-safe contracts for node outputs
- **Strategy Pattern**: Node-specific execution strategies
- **Observer Pattern**: Execution state tracking and history
- **Dependency Resolution**: Runtime input resolution system

## Core Components

### 1. Envelope System (`envelope.py`)

Provides unified message passing system with type-safe output contracts:

```python
@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication"""
    id: str
    produced_by: str
    content_type: ContentType
    body: Any
    meta: dict[str, Any]

```

**Key Features:**
- Immutable message envelopes
- Built-in serialization support
- Unified messaging across all node types
- Content type support for different data formats

### 2. Execution Context (`execution_context.py`)

Manages runtime state during diagram execution:

```python
class ExecutionContext:
    """Runtime context for diagram execution"""
    
    def __init__(self, diagram: ExecutableDiagram, execution_id: str):
        self.diagram = diagram
        self.execution_id = execution_id
        self.node_outputs: dict[NodeID, Envelope] = {}
        self.metadata: dict[str, Any] = {}
    
    def store_output(self, node_id: NodeID, output: Envelope):
        """Store node execution results"""
    
    def get_output(self, node_id: NodeID) -> Envelope | None:
        """Retrieve node output by ID"""
```

**Key Responsibilities:**
- Maintains node execution results
- Tracks execution metadata
- Provides output retrieval interface
- Manages execution scope

### 3. Execution State Manager (`execution_state_manager.py`)

Coordinates state persistence and retrieval:

```python
class ExecutionStateManager:
    """Manages execution state lifecycle"""
    
    async def save_state(self, execution_id: str, state: ExecutionState):
        """Persist execution state"""
    
    async def load_state(self, execution_id: str) -> ExecutionState:
        """Restore execution state"""
    
    async def update_node_status(self, execution_id: str, node_id: NodeID, status: str):
        """Update individual node status"""
```

**Features:**
- Asynchronous state operations
- Atomic state updates
- State recovery for resumption
- Transaction support

### 4. Execution Tracker (`execution_tracker.py`)

Maintains execution history and analytics:

```python
class ExecutionTracker:
    """Tracks execution progress and history"""
    
    def record_node_start(self, node_id: NodeID, timestamp: datetime):
        """Record node execution start"""
    
    def record_node_complete(self, node_id: NodeID, output: Envelope):
        """Record node completion with output"""
    
    def get_execution_metrics(self) -> ExecutionMetrics:
        """Calculate execution statistics"""
```

**Tracking Capabilities:**
- Node execution timings
- Success/failure rates
- Performance metrics
- Execution paths
- Resource utilization

### 5. Dynamic Order Calculator (`dynamic_order_calculator.py`)

Determines runtime execution order based on dependencies:

```python
class DynamicOrderCalculator:
    """Calculates node execution order dynamically"""
    
    def get_ready_nodes(self, 
                       completed: set[NodeID], 
                       failed: set[NodeID]) -> list[NodeID]:
        """Get nodes ready for execution"""
    
    def calculate_dependencies(self, node_id: NodeID) -> set[NodeID]:
        """Calculate node dependencies"""
```

**Scheduling Features:**
- Topological sorting
- Parallel execution detection
- Conditional branch handling
- Cycle detection
- Priority-based scheduling

### 6. Node Strategy (`node_strategy.py`)

Defines execution strategies for different node types:

```python
class NodeStrategyProtocol(Protocol):
    """Protocol for node execution strategies"""
    
    async def execute(self, 
                     node: ExecutableNode, 
                     context: ExecutionContext) -> Envelope:
        """Execute node with strategy"""
    
    def can_handle(self, node_type: str) -> bool:
        """Check if strategy handles node type"""
```

**Strategy Types:**
- `PersonJobStrategy` - LLM interaction nodes
- `ConditionStrategy` - Conditional branching
- `CodeJobStrategy` - Code execution
- `ApiJobStrategy` - External API calls
- `SubDiagramStrategy` - Nested diagram execution

### 7. Runtime Resolver (`runtime_resolver.py`)

Resolves inputs and transformations at runtime:

```python
class RuntimeResolver:
    """Resolves runtime inputs for nodes"""
    
    def resolve_inputs(self, 
                      node: ExecutableNode, 
                      context: ExecutionContext) -> dict[str, Any]:
        """Resolve all inputs for a node"""
    
    def apply_transformations(self, 
                            value: Any, 
                            rules: list[TransformRule]) -> Any:
        """Apply transformation rules to values"""
```

**Resolution Features:**
- Input mapping from outputs
- Default value handling
- Type coercion
- Transformation pipelines
- Template resolution

## Interfaces and Protocols

### Envelope
Primary message format for all node outputs:
```python
@dataclass(frozen=True)
class Envelope:
    id: str                       # Unique envelope ID
    produced_by: str              # Source node ID
    content_type: ContentType     # Type of content
    body: Any                     # Actual content
    meta: dict[str, Any]          # Additional metadata
    node_id: NodeID              # Source node identifier
    timestamp: datetime          # Execution timestamp
    
    def get_output(self, key: str, default: Any = None) -> Any
    def has_error(self) -> bool
    def to_dict(self) -> dict[str, Any]
```

### ExecutionStateProtocol
Contract for execution state persistence:
```python
class ExecutionStateProtocol(Protocol):
    execution_id: str
    status: ExecutionStatus
    node_states: dict[NodeID, NodeState]
    start_time: datetime
    end_time: datetime | None
    
    async def persist(self) -> None
    async def restore(self) -> None
```

## Usage Examples

### Basic Execution Flow
```python
# Initialize execution context
context = ExecutionContext(diagram, execution_id="exec-123")

# Calculate ready nodes
calculator = DynamicOrderCalculator(diagram)
ready_nodes = calculator.get_ready_nodes(
    completed=context.completed_nodes,
    failed=context.failed_nodes
)

# Execute nodes with strategies
for node_id in ready_nodes:
    node = diagram.get_node(node_id)
    strategy = strategy_registry.get_strategy(node.type)
    
    # Resolve inputs
    inputs = runtime_resolver.resolve_inputs(node, context)
    
    # Execute with tracking
    tracker.record_node_start(node_id, datetime.now())
    output = await strategy.execute(node, context, inputs)
    tracker.record_node_complete(node_id, output)
    
    # Store output
    context.store_output(node_id, output)
```

### Custom Node Output
```python
@dataclass
class CustomOutput(BaseNodeOutput[dict]):
    """Custom output for specialized node"""
    
    def validate(self) -> bool:
        """Validate output structure"""
        return "required_field" in self.value
    
    def transform(self) -> Any:
        """Transform for downstream consumption"""
        return self.value.get("data", {})
```

### State Management
```python
# Save execution state
state_manager = ExecutionStateManager(state_store)
await state_manager.save_state(execution_id, context.to_state())

# Resume execution
restored_state = await state_manager.load_state(execution_id)
context = ExecutionContext.from_state(restored_state)
```

## Development Guidelines

### Adding New Output Types
1. Create envelopes with appropriate content types
2. Use EnvelopeFactory for consistent creation
3. Store metadata in the meta field
4. Add validation logic if needed
5. Register with output factory

### Creating Execution Strategies
1. Implement `NodeStrategyProtocol`
2. Define `can_handle` for node type matching
3. Implement `execute` with proper error handling
4. Register strategy in registry
5. Add unit tests

### Extending Runtime Resolution
1. Implement transformation rules
2. Add to transformation registry
3. Define precedence if needed
4. Handle edge cases
5. Document transformation behavior

## Dependencies

**Internal:**
- `dipeo.diagram_generated` - Generated node types
- `dipeo.core.ports` - Port interfaces
- `dipeo.core.base` - Base exceptions

**External:**
- Python 3.13+ standard library
- `typing` - Type hints and protocols
- `dataclasses` - Data structures
- `asyncio` - Asynchronous execution

## Testing

### Unit Testing
```python
def test_node_output_protocol():
    """Test output protocol implementation"""
    output = TextOutput(
        value="test",
        node_id="node-1",
        metadata={"key": "value"}
    )
    assert output.has_error() is False
    assert output.get_output("key") == "value"
```

### Integration Testing
```python
async def test_execution_flow():
    """Test complete execution flow"""
    context = ExecutionContext(test_diagram, "test-exec")
    calculator = DynamicOrderCalculator(test_diagram)
    
    # Execute all nodes
    while ready := calculator.get_ready_nodes(context.completed_nodes):
        for node_id in ready:
            output = await execute_node(node_id, context)
            context.store_output(node_id, output)
```

## Performance Considerations

- **Output Storage**: Use lazy loading for large outputs
- **State Persistence**: Batch state updates when possible
- **Resolution Caching**: Cache resolved inputs within execution
- **Parallel Execution**: Identify independent nodes for parallelization
- **Memory Management**: Clean up outputs after consumption

## Migration Notes

- ✅ Legacy `node_output` module replaced with unified envelope system (2025-08-14)
- ✅ All outputs now use immutable `Envelope` instances
- Old `ExecutionState` class deprecated in favor of `ExecutionContext`
- Direct state updates replaced with event-based state management
- Synchronous execution being migrated to async throughout