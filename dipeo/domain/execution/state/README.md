# State Management

## Overview

The `state/` module manages node execution states and history. It separates concerns into:

1. **StateTracker**: Node states for UI visualization and iteration limits
2. **ExecutionTracker**: Immutable execution history for reporting and analysis
3. **Ports**: Domain ports for persistence (future)

**Key Principle:** State tracking is for **UI visualization and reporting only**. Execution flow is driven by **tokens**, not status.

## Architecture

```
┌─────────────────────────────────┐
│       StateTracker              │
│  - Node states (UI)             │
│  - Iteration counts             │
│  - Metadata                     │
│  - Thread-safe                  │
└─────────────────────────────────┘
            │ uses
            ▼
┌─────────────────────────────────┐
│     ExecutionTracker            │
│  - Immutable history            │
│  - Execution records            │
│  - Runtime state                │
│  - Summaries                    │
└─────────────────────────────────┘
```

## StateTracker

**Location:** `dipeo/domain/execution/state/state_tracker.py:20`

Tracks node execution states, primarily for UI visualization.

### Responsibilities

1. **Node State Transitions**: PENDING → RUNNING → COMPLETED/FAILED/MAXITER/SKIPPED
2. **Execution Counting**: Track how many times each node has executed
3. **Iteration Limits**: Enforce max iterations per epoch
4. **Result Storage**: Store and retrieve node outputs
5. **Thread Safety**: Lock-based synchronization

### Key Operations

#### State Transitions

```python
from dipeo.domain.execution.state import StateTracker

tracker = StateTracker()

# Initialize
tracker.initialize_node(node_id)
# State: PENDING

# Start execution
exec_count = tracker.transition_to_running(node_id, epoch=0)
# State: RUNNING, returns execution count

# Success
tracker.transition_to_completed(node_id, output=envelope)
# State: COMPLETED

# Failure
tracker.transition_to_failed(node_id, error="Error message")
# State: FAILED

# Max iterations reached
tracker.transition_to_maxiter(node_id, output=envelope)
# State: MAXITER_REACHED

# Skipped (conditional branch not taken)
tracker.transition_to_skipped(node_id)
# State: SKIPPED

# Reset for next iteration
tracker.reset_node(node_id)
# State: PENDING (execution count NOT reset)
```

#### State Queries

```python
# Get node state
state = tracker.get_node_state(node_id)
# Returns: NodeState(status=Status.COMPLETED, error=None)

# Get all states
all_states = tracker.get_all_node_states()
# Returns: {node_id: NodeState, ...}

# Query by status
completed = tracker.get_completed_nodes()  # [node_id, ...]
running = tracker.get_running_nodes()      # [node_id, ...]
failed = tracker.get_failed_nodes()        # [node_id, ...]

# Check if any nodes are running
has_running = tracker.has_running_nodes()  # bool
```

#### Execution Counts

```python
# Get execution count (cumulative)
count = tracker.get_node_execution_count(node_id)

# Check iteration limit
can_run = tracker.can_execute_in_loop(
    node_id,
    epoch=0,
    max_iteration=10  # Node-specific limit (e.g., PersonJob)
)

# Get iterations in specific epoch
iterations = tracker.get_iterations_in_epoch(node_id, epoch=0)
```

#### Result Access

```python
# Get node result
result = tracker.get_node_result(node_id)
# Returns: {"value": ..., "metadata": {...}} or None

# Get node output (Envelope)
output = tracker.get_node_output(node_id)
# Returns: Envelope or None
```

#### Metadata

```python
# Set metadata
tracker.set_node_metadata(node_id, "key", "value")

# Get metadata
metadata = tracker.get_node_metadata(node_id)
# Returns: {"key": "value"}
```

### Thread Safety

StateTracker uses a `threading.Lock` for thread-safe operations:

```python
with self._lock:
    self._node_states[node_id] = NodeState(status=Status.RUNNING)
```

All public methods are thread-safe.

### Iteration Limits

StateTracker tracks iterations per epoch:

```python
# Internal structure
self._node_iterations_per_epoch: dict[tuple[NodeID, int], int]

# Example: node "A" has executed 3 times in epoch 0
# {("A", 0): 3}
```

**Default max iterations per epoch:** 100

**Node-specific limits:** PersonJobNode has `max_iteration` field

```python
# Check if node can execute
can_run = tracker.can_execute_in_loop(
    node_id="person-job-1",
    epoch=0,
    max_iteration=5  # PersonJob-specific limit
)
# Returns False if node has executed 5+ times in epoch 0
```

### Persistence (Future)

StateTracker supports loading persisted state:

```python
# Load from persistence
tracker.load_states(node_states, execution_tracker)
```

This will be used when implementing execution resume.

## ExecutionTracker

**Location:** `dipeo/domain/execution/state/execution_tracker.py:54`

Separates immutable execution history from mutable runtime state.

### Responsibilities

1. **Immutable History**: Record of all node executions
2. **Runtime State**: Current flow status (READY, RUNNING, WAITING, BLOCKED)
3. **Execution Counting**: Track execution attempts
4. **Summaries**: Aggregate execution metrics

### Core Types

#### NodeExecutionRecord

**Location:** `dipeo/domain/execution/state/execution_tracker.py:23`

```python
@dataclass
class NodeExecutionRecord:
    node_id: NodeID
    execution_number: int        # 1st, 2nd, 3rd execution
    started_at: datetime
    ended_at: datetime | None
    status: CompletionStatus     # SUCCESS, FAILED, MAX_ITER, SKIPPED
    output: Envelope | None
    error: str | None
    token_usage: dict[str, int] | None
    duration: float              # Seconds

    def is_complete(self) -> bool: ...
    def was_successful(self) -> bool: ...
```

Immutable record of a single node execution.

#### NodeRuntimeState

**Location:** `dipeo/domain/execution/state/execution_tracker.py:42`

```python
@dataclass
class NodeRuntimeState:
    node_id: NodeID
    flow_status: FlowStatus      # READY, RUNNING, WAITING, BLOCKED
    is_active: bool
    dependencies_met: bool
    last_check: datetime

    def can_execute(self) -> bool: ...
```

Mutable runtime state for flow control (not used by execution engine - tokens handle this).

### Key Operations

#### Execution Lifecycle

```python
from dipeo.domain.execution.state import ExecutionTracker, CompletionStatus

tracker = ExecutionTracker()

# Start execution
exec_num = tracker.start_execution(node_id)
# Returns: 1 (first execution)
# Creates: NodeExecutionRecord with started_at

# Complete execution
tracker.complete_execution(
    node_id,
    status=CompletionStatus.SUCCESS,
    output=envelope,
    token_usage={"input": 100, "output": 50}
)
# Updates: Record with ended_at, status, output, duration

# Failed execution
tracker.complete_execution(
    node_id,
    status=CompletionStatus.FAILED,
    error="Connection timeout"
)
```

#### History Queries

```python
# Get execution count
count = tracker.get_execution_count(node_id)  # int

# Check if ever executed
has_run = tracker.has_executed(node_id)  # bool

# Get last output
output = tracker.get_last_output(node_id)  # Envelope or None

# Get all execution records for a node
records = tracker.get_node_execution_history(node_id)
# Returns: list[NodeExecutionRecord]

# Get execution summary
summary = tracker.get_execution_summary()
# Returns: {
#     "total_executions": 42,
#     "successful_executions": 40,
#     "failed_executions": 2,
#     "success_rate": 0.95,
#     "total_duration": 125.5,
#     "total_tokens": {"input": 5000, "output": 3000, "cached": 1000},
#     "nodes_executed": 10,
#     "execution_order": [node_id, ...]
# }
```

#### Runtime State (Not Used by Execution Engine)

```python
# Get runtime state
state = tracker.get_runtime_state(node_id)
# Returns: NodeRuntimeState

# Update runtime state
tracker.update_runtime_state(node_id, FlowStatus.RUNNING)

# Reset for iteration
tracker.reset_for_iteration(node_id)
# Sets: flow_status=READY, dependencies_met=True, is_active=True
```

**Note:** Runtime state is maintained but **not used** by the execution engine. Token flow controls execution.

#### Clear History

```python
# Clear all history (for testing)
tracker.clear_history()
```

### Execution vs Iteration

**Execution Count**: Cumulative count across all iterations
```python
# Node executes 3 times in epoch 0, 2 times in epoch 1
execution_count = 5  # Total
```

**Iteration Count**: Per-epoch count (tracked by StateTracker)
```python
# StateTracker
iterations_epoch_0 = 3
iterations_epoch_1 = 2
```

### CompletionStatus

**From:** `dipeo.diagram_generated.enums.CompletionStatus`

```python
class CompletionStatus(Enum):
    SUCCESS = "success"          # Completed successfully
    FAILED = "failed"            # Execution failed
    MAX_ITER = "max_iter"        # Max iterations reached
    SKIPPED = "skipped"          # Skipped (condition branch)
```

### FlowStatus

**From:** `dipeo.diagram_generated.enums.FlowStatus`

```python
class FlowStatus(Enum):
    READY = "ready"              # Ready to execute
    RUNNING = "running"          # Currently executing
    WAITING = "waiting"          # Waiting for dependencies
    BLOCKED = "blocked"          # Blocked (failed dependency)
```

## Ports

**Location:** `dipeo/domain/execution/state/ports.py`

Domain ports for state persistence (future implementation).

### ExecutionStateRepository

```python
@runtime_checkable
class ExecutionStateRepository(Protocol):
    """Repository for execution state persistence."""

    async def create_execution(
        self, execution_id: ExecutionID, diagram_id: DiagramID | None = None, ...
    ) -> ExecutionState: ...

    async def get_execution(self, execution_id: str) -> ExecutionState | None: ...

    async def save_execution(self, state: ExecutionState) -> None: ...

    async def update_status(self, execution_id: str, status: Status, ...) -> None: ...

    async def get_node_output(self, execution_id: str, node_id: str) -> dict | None: ...

    async def update_node_output(self, execution_id: str, node_id: str, ...) -> None: ...

    # ... more methods
```

Used for:
- Persisting execution state to database
- Loading execution state for resume
- Querying historical executions

### ExecutionStateService

```python
@runtime_checkable
class ExecutionStateService(Protocol):
    """High-level service for execution state management."""

    async def start_execution(...) -> ExecutionState: ...
    async def finish_execution(...) -> None: ...
    async def update_node_execution(...) -> None: ...
    async def append_token_usage(...) -> None: ...
    async def get_execution_state(...) -> ExecutionState | None: ...
```

Higher-level abstractions over the repository.

### ExecutionCachePort

```python
@runtime_checkable
class ExecutionCachePort(Protocol):
    """Optional cache layer for execution state."""

    async def get_state_from_cache(...) -> ExecutionState | None: ...
    async def create_execution_in_cache(...) -> ExecutionState: ...
    async def persist_final_state(...) -> None: ...
```

For caching execution state in memory or Redis.

**Note:** These are domain ports (protocols). Implementations live in the infrastructure layer.

## Usage Patterns

### Basic Node Execution

```python
# 1. Initialize
tracker = StateTracker()
tracker.initialize_node(node_id)

# 2. Start execution
exec_count = tracker.transition_to_running(node_id, epoch=0)
print(f"Execution #{exec_count}")

# 3. Execute node
result = execute_node(node)

# 4. Complete
output = EnvelopeFactory.create(body=result)
tracker.transition_to_completed(node_id, output=output)

# 5. Query
state = tracker.get_node_state(node_id)
assert state.status == Status.COMPLETED
```

### Loop with Iteration Limits

```python
epoch = 0
max_iterations = 10

while True:
    # Check iteration limit
    if not tracker.can_execute_in_loop(node_id, epoch, max_iterations):
        tracker.transition_to_maxiter(node_id)
        break

    # Execute
    tracker.transition_to_running(node_id, epoch)
    result = execute_node(node)
    output = EnvelopeFactory.create(body=result)
    tracker.transition_to_completed(node_id, output=output)

    # Check exit condition
    if should_exit(result):
        break

    # Reset for next iteration
    tracker.reset_node(node_id)
```

### Error Handling

```python
try:
    tracker.transition_to_running(node_id, epoch)
    result = execute_node(node)
    output = EnvelopeFactory.create(body=result)
    tracker.transition_to_completed(node_id, output=output)
except Exception as e:
    tracker.transition_to_failed(node_id, error=str(e))
```

### Execution Summary

```python
# After execution completes
summary = tracker.get_tracker().get_execution_summary()

print(f"Total executions: {summary['total_executions']}")
print(f"Success rate: {summary['success_rate']:.2%}")
print(f"Total duration: {summary['total_duration']:.2f}s")
print(f"Tokens used: {summary['total_tokens']}")
```

## Design Rationale

### Why Separate StateTracker and ExecutionTracker?

**StateTracker:**
- Mutable, UI-focused
- Tracks current status (PENDING, RUNNING, COMPLETED)
- Manages iteration limits
- Thread-safe for concurrent access

**ExecutionTracker:**
- Immutable history
- Records all executions
- Used for reporting, analysis, conditions
- Single-threaded (called from StateTracker)

This separation allows:
- Clear ownership (StateTracker owns ExecutionTracker)
- Different concerns (UI vs history)
- Easier testing (mock ExecutionTracker independently)

### Why Track State if Tokens Drive Execution?

**State is for UI and reporting, NOT execution logic.**

```python
# Execution engine uses tokens
if ctx.tokens.has_new_inputs(node_id):
    execute_node(node)

# State tracking is parallel (for UI)
ctx.state.transition_to_running(node_id, epoch)
```

Benefits:
- UI can show status without affecting execution
- Execution logic stays simple (tokens only)
- State can be added/removed without changing execution flow

### Why Iteration Limits in StateTracker?

Iteration limits are a **safety mechanism**, not execution logic:

```python
# Check limit before executing
if not tracker.can_execute_in_loop(node_id, epoch, max_iteration):
    # Safety: prevent infinite loops
    tracker.transition_to_maxiter(node_id)
    break
```

It's a domain rule separate from token flow.

## Performance Considerations

- **Thread Safety**: StateTracker uses locks (potential contention)
- **Execution Records**: Stored in memory (grows with execution count)
- **Iteration Tracking**: O(1) lookup per (node, epoch) key
- **State Queries**: O(1) for single node, O(N) for all nodes

For long-running executions, consider:
- Periodic cleanup of old records
- Disk-based persistence (future)
- Separate service for historical queries

## Testing

```python
def test_state_transitions():
    tracker = StateTracker()
    tracker.initialize_node("node-1")

    # Test transition
    tracker.transition_to_running("node-1", epoch=0)
    state = tracker.get_node_state("node-1")
    assert state.status == Status.RUNNING

    # Test completion
    output = EnvelopeFactory.create(body="result")
    tracker.transition_to_completed("node-1", output=output)
    assert tracker.get_node_result("node-1")["value"] == "result"

def test_iteration_limits():
    tracker = StateTracker()

    # Execute 10 times
    for i in range(10):
        assert tracker.can_execute_in_loop("node-1", epoch=0, max_iteration=10)
        tracker.transition_to_running("node-1", epoch=0)
        tracker.transition_to_completed("node-1")
        tracker.reset_node("node-1")

    # 11th should fail
    assert not tracker.can_execute_in_loop("node-1", epoch=0, max_iteration=10)
```

## Related Components

- **ExecutionContext** (`context/execution_context.py`): Uses StateTracker
- **TokenManager** (`tokens/token_manager.py`): Drives execution (not state)
- **Envelope** (`messaging/envelope.py`): Stores outputs

## Future Enhancements

1. **Persistence**: Implement ports for database storage
2. **Caching**: Redis-based state cache
3. **Resume**: Load persisted state to resume execution
4. **Streaming**: Stream state updates to UI via WebSocket
5. **Metrics**: Prometheus-style metrics export
