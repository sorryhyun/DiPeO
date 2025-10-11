# Execution Context Protocol

## Overview

The `ExecutionContext` protocol defines the contract for managing runtime execution state during diagram execution. It serves as the primary interface between the execution engine and domain-level components, providing access to:

- Diagram structure and metadata
- Token-based flow control
- State tracking (UI visualization)
- Variable management (loops, conditions)
- Input/output operations

## Implementation

**Location:** `dipeo/domain/execution/context/execution_context.py:15`

```python
from typing import Protocol
from dipeo.diagram_generated import NodeID
from dipeo.domain.execution.messaging.envelope import Envelope
from dipeo.domain.execution.state.state_tracker import StateTracker
from dipeo.domain.execution.tokens.token_manager import TokenManager

class ExecutionContext(Protocol):
    """Manages runtime execution state with token-based flow control."""

    # Core References
    diagram: ExecutableDiagram
    execution_id: str

    # Manager Components
    state: StateTracker      # State management (UI)
    tokens: TokenManager     # Token flow control

    def current_epoch(self) -> int:
        """Get the current execution epoch."""

    def get_variable(self, name: str) -> Any:
        """Get a variable value (for conditions and expressions)."""

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value (for loop indices and branch tracking)."""

    def get_variables(self) -> dict[str, Any]:
        """Get all variables (for expression evaluation)."""

    def consume_inbound(self, node_id: NodeID) -> dict[str, Envelope]:
        """Consume inbound tokens for a node."""

    def emit_outputs_as_tokens(self, node_id: NodeID, outputs: dict[str, Envelope]) -> None:
        """Emit node outputs as tokens on outgoing edges."""
```

## Why a Protocol?

Using a `Protocol` (structural subtyping) instead of an abstract base class provides:

1. **Decoupling**: Domain layer doesn't depend on application layer
2. **Flexibility**: Multiple implementations can exist without inheritance
3. **Type Safety**: Static type checkers verify conformance
4. **Clean Architecture**: Domain defines contracts, application implements

The actual implementation lives in the application layer (`dipeo.application.execution.engine`).

## Core Attributes

### diagram: ExecutableDiagram

Reference to the diagram being executed. Provides access to:
- Nodes: `diagram.get_node(node_id)`
- Edges: `diagram.edges`
- Start node: `diagram.start_node`
- Metadata: `diagram.name`, `diagram.id`

### execution_id: str

Unique identifier for this execution instance. Used for:
- Logging and debugging
- Persistence (future)
- UI updates
- Audit trails

### state: StateTracker

Manages node execution states and history. See [state/README.md](../state/README.md) for details.

**Key operations:**
```python
# Transition states (for UI)
ctx.state.transition_to_running(node_id, epoch)
ctx.state.transition_to_completed(node_id, output)
ctx.state.transition_to_failed(node_id, error)

# Query state
state = ctx.state.get_node_state(node_id)
result = ctx.state.get_node_result(node_id)
count = ctx.state.get_node_execution_count(node_id)
```

### tokens: TokenManager

Manages token flow through the execution graph. See [tokens/README.md](../tokens/README.md) for details.

**Key operations:**
```python
# Check readiness
is_ready = ctx.tokens.has_new_inputs(node_id, join_policy="all")

# Publish tokens
ctx.tokens.emit_outputs(node_id, outputs, epoch)

# Consume tokens
inputs = ctx.tokens.consume_inbound(node_id)
```

## Core Methods

### current_epoch() -> int

Returns the current execution epoch. Epochs are used for loop iterations:

- Epoch 0: Initial execution (before any loops)
- Epoch 1+: Loop iterations

**Usage:**
```python
epoch = ctx.current_epoch()
ctx.state.transition_to_running(node_id, epoch)
```

### Variable Management

Variables store runtime state like loop indices and condition results.

**get_variable(name: str) -> Any**

Retrieve a variable value:
```python
loop_index = ctx.get_variable("loop_index")
branch_taken = ctx.get_variable("condition_result")
```

**set_variable(name: str, value: Any) -> None**

Set a variable value:
```python
ctx.set_variable("loop_index", 5)
ctx.set_variable("condition_result", True)
```

**get_variables() -> dict[str, Any]**

Get all variables (for expression evaluation):
```python
vars = ctx.get_variables()
result = eval(expression, vars)
```

### consume_inbound(node_id: NodeID) -> dict[str, Envelope]

Atomically consume tokens from incoming edges.

**Delegates to:** `ctx.tokens.consume_inbound(node_id)`

**Returns:** Dictionary mapping port names to envelopes

**Usage:**
```python
# Before executing a node
token_inputs = ctx.consume_inbound(node_id)

# token_inputs = {
#     "default": Envelope(body="value"),
#     "input2": Envelope(body={"key": "data"})
# }
```

### emit_outputs_as_tokens(node_id: NodeID, outputs: dict[str, Envelope]) -> None

Publish tokens on all outgoing edges from a node.

**Delegates to:** `ctx.tokens.emit_outputs(node_id, outputs)`

**Usage:**
```python
# After node execution
outputs = {
    "default": EnvelopeFactory.create(body=result),
    "error": EnvelopeFactory.create(body=error_msg) if error else None
}
ctx.emit_outputs_as_tokens(node_id, outputs)
```

For condition nodes, use special ports:
```python
# Condition node outputs
outputs = {
    "condtrue": EnvelopeFactory.create(body=True) if condition else None,
    "condfalse": EnvelopeFactory.create(body=False) if not condition else None
}
ctx.emit_outputs_as_tokens(node_id, outputs)
```

## Usage Patterns

### Basic Node Execution

```python
def execute_node(node_id: NodeID, ctx: ExecutionContext):
    # 1. Check readiness
    if not ctx.tokens.has_new_inputs(node_id):
        return

    # 2. Transition to running (UI)
    ctx.state.transition_to_running(node_id, ctx.current_epoch())

    # 3. Consume tokens
    token_inputs = ctx.consume_inbound(node_id)

    # 4. Resolve inputs
    resolved = resolve_inputs(node, ctx.diagram, ctx)

    # 5. Execute
    result = perform_work(resolved)

    # 6. Create output
    output = EnvelopeFactory.create(body=result, node_id=node_id)

    # 7. Update state (UI)
    ctx.state.transition_to_completed(node_id, output)

    # 8. Emit tokens
    ctx.emit_outputs_as_tokens(node_id, {"default": output})
```

### Loop Execution

```python
def execute_loop(loop_node_id: NodeID, ctx: ExecutionContext):
    # Enter new epoch
    epoch = ctx.tokens.begin_epoch()
    ctx.set_variable("loop_index", 0)

    # Execute loop body
    for i in range(max_iterations):
        ctx.set_variable("loop_index", i)

        # Execute loop nodes
        for node_id in loop_body:
            if ctx.tokens.has_new_inputs(node_id, epoch=epoch):
                execute_node(node_id, ctx)

        # Check iteration limit
        if not ctx.state.can_execute_in_loop(node_id, epoch, max_iteration):
            ctx.state.transition_to_maxiter(node_id)
            break
```

### Condition Handling

```python
def execute_condition(node_id: NodeID, ctx: ExecutionContext):
    # Evaluate condition
    condition_result = evaluate_condition(node, ctx)

    # Store result
    ctx.set_variable(f"{node_id}_result", condition_result)

    # Emit on correct branch
    if condition_result:
        outputs = {"condtrue": EnvelopeFactory.create(body=True)}
    else:
        outputs = {"condfalse": EnvelopeFactory.create(body=False)}

    ctx.emit_outputs_as_tokens(node_id, outputs)
```

## Design Considerations

### Why Separate state and tokens?

**state**: For UI visualization and reporting
- Tracks node status (PENDING, RUNNING, COMPLETED)
- Stores execution history
- Provides execution counts and durations
- NOT used for execution flow decisions

**tokens**: For execution flow control
- Determines node readiness
- Manages data flow between nodes
- Handles join policies and epochs
- Drives the execution engine

This separation allows the execution engine to ignore status and focus purely on token availability.

### Why Protocol Instead of ABC?

**Advantages:**
- Domain layer stays pure (no application dependencies)
- Multiple implementations possible
- Duck typing for tests and mocks
- Structural subtyping is more flexible

**Disadvantages:**
- No runtime checking (use `@runtime_checkable` if needed)
- Must manually ensure all methods are implemented

### Variable Scope

Variables are execution-scoped:
- Persist across node executions within the same execution
- Used for loop indices, condition results, temporary state
- NOT persisted between diagram runs
- NOT shared between parallel executions

## Related Components

- **TokenManager** (`tokens/token_manager.py`): Token-based flow control
- **StateTracker** (`state/state_tracker.py`): State management for UI
- **Envelope** (`messaging/envelope.py`): Message passing
- **resolve_inputs** (`resolution/api.py`): Input resolution

## Implementation Reference

The application layer implements this protocol in:
```
dipeo/application/execution/engine/execution_engine.py
```

The implementation uses:
- `StateTracker` for state management
- `TokenManager` for token flow
- `dict[str, Any]` for variables

## Type Checking

Use `TYPE_CHECKING` to avoid circular imports:

```python
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.domain.execution.state.state_tracker import StateTracker
    from dipeo.domain.execution.tokens.token_manager import TokenManager

class ExecutionContext(Protocol):
    diagram: "ExecutableDiagram"
    state: "StateTracker"
    tokens: "TokenManager"
    ...
```

This prevents import cycles while maintaining type safety.
