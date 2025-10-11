# State Management - Unified State Tracker

## Overview

The `state/` module provides a **unified state tracking system** that consolidates UI state, execution history, and iteration limits into a single source of truth.

**Key Change (2025-10-11):** The previous `ExecutionTracker` and `StateTracker` classes have been unified into `UnifiedStateTracker` to eliminate redundancy and prevent state divergence.

## Architecture

```
┌─────────────────────────────────────────────┐
│       UnifiedStateTracker                   │
│  Single Source of Truth                     │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │ UI State                           │    │
│  │ - Node states (PENDING, RUNNING...)│    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │ Execution History                  │    │
│  │ - Immutable execution records      │    │
│  │ - Execution counts                 │    │
│  │ - Last outputs                     │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │ Iteration Limits                   │    │
│  │ - Per-epoch tracking               │    │
│  │ - Max iteration enforcement        │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │ Metadata                           │    │
│  │ - Arbitrary key-value storage      │    │
│  └────────────────────────────────────┘    │
│                                              │
│  Thread-safe with internal lock             │
└─────────────────────────────────────────────┘
```

## UnifiedStateTracker

**Location:** `dipeo/domain/execution/state/unified_state_tracker.py`

The unified tracker consolidates all state tracking responsibilities:
- UI state tracking (for visualization)
- Execution history (for reporting)
- Iteration limits (for safety)
- Node metadata (for arbitrary storage)
- Thread safety (for concurrent access)

### Key Features

1. **Single Source of Truth**: No duplication, no divergence
2. **Thread-Safe**: All operations protected by internal lock
3. **Clear Separation**: Internal structure separates concerns
4. **Backward Compatible**: Aliases for old class names
5. **Comprehensive**: All features from both previous trackers

### Core Data Structures

#### NodeState
```python
@dataclass
class NodeState:
    """Current state of a node for UI visualization."""
    status: Status  # PENDING, RUNNING, COMPLETED, FAILED, etc.
    error: str | None = None
```

#### NodeExecutionRecord
```python
@dataclass
class NodeExecutionRecord:
    """Immutable record of a single node execution."""
    node_id: NodeID
    execution_number: int
    started_at: datetime
    ended_at: datetime | None
    status: CompletionStatus  # SUCCESS, FAILED, MAX_ITER, SKIPPED
    output: Envelope | None
    error: str | None
    token_usage: dict[str, int] | None = None
    duration: float = 0.0
```

## Usage

### Basic Usage

```python
from dipeo.domain.execution.state import UnifiedStateTracker
from dipeo.domain.execution.messaging import EnvelopeFactory

tracker = UnifiedStateTracker()

# Initialize node
tracker.initialize_node("node-1")

# Start execution
exec_count = tracker.transition_to_running("node-1", epoch=0)
print(f"Execution #{exec_count}")

# Complete execution
output = EnvelopeFactory.create(body="result")
tracker.transition_to_completed("node-1", output=output, token_usage={"input": 100})

# Query state
state = tracker.get_node_state("node-1")
print(f"Status: {state.status}")  # COMPLETED

# Get result
result = tracker.get_node_result("node-1")
print(f"Result: {result['value']}")  # "result"
```

### State Transitions

```python
# Initialize to PENDING
tracker.initialize_node(node_id)

# Transition to RUNNING
exec_count = tracker.transition_to_running(node_id, epoch=0)

# Transition to COMPLETED (success)
tracker.transition_to_completed(node_id, output=envelope, token_usage=tokens)

# Transition to FAILED
tracker.transition_to_failed(node_id, error="Error message")

# Transition to MAXITER_REACHED
tracker.transition_to_maxiter(node_id, output=envelope)

# Transition to SKIPPED (conditional branch not taken)
tracker.transition_to_skipped(node_id)

# Reset to PENDING (for next iteration)
tracker.reset_node(node_id)
```

### State Queries

```python
# Get single node state
state = tracker.get_node_state(node_id)

# Get all node states
all_states = tracker.get_all_node_states()

# Query by status
completed = tracker.get_completed_nodes()
running = tracker.get_running_nodes()
failed = tracker.get_failed_nodes()

# Check if any nodes are running
has_running = tracker.has_running_nodes()
```

### Execution History

```python
# Get execution count (cumulative)
count = tracker.get_execution_count(node_id)

# Check if ever executed
has_run = tracker.has_executed(node_id)

# Get last output
output = tracker.get_last_output(node_id)

# Get node result (body + metadata)
result = tracker.get_node_result(node_id)

# Get full execution history
history = tracker.get_node_execution_history(node_id)
for record in history:
    print(f"Execution #{record.execution_number}: {record.status}")

# Get execution summary
summary = tracker.get_execution_summary()
print(f"Total: {summary['total_executions']}")
print(f"Success rate: {summary['success_rate']:.2%}")
print(f"Tokens: {summary['total_tokens']}")
```

### Iteration Limits

```python
# Check if node can execute (default limit: 100 per epoch)
can_run = tracker.can_execute_in_loop(node_id, epoch=0)

# Check with custom limit
can_run = tracker.can_execute_in_loop(node_id, epoch=0, max_iteration=10)

# Get iterations in specific epoch
iterations = tracker.get_iterations_in_epoch(node_id, epoch=0)
```

### Metadata

```python
# Set metadata
tracker.set_node_metadata(node_id, "key", "value")

# Get metadata (returns copy)
metadata = tracker.get_node_metadata(node_id)
```

### Persistence

```python
# Load persisted states
tracker.load_states(
    node_states=persisted_states,
    execution_records=persisted_records,
    execution_counts=persisted_counts,
    last_outputs=persisted_outputs
)

# Clear all history (for testing)
tracker.clear_history()
```

## Backward Compatibility

The unified tracker maintains backward compatibility with old code:

```python
# Old imports still work (aliases)
from dipeo.domain.execution.state import StateTracker, ExecutionTracker

# Both are now aliases for UnifiedStateTracker
tracker1 = StateTracker()  # UnifiedStateTracker
tracker2 = ExecutionTracker()  # UnifiedStateTracker

# Old method names still work
tracker.get_node_execution_count(node_id)  # Alias for get_execution_count()
tracker.get_node_output(node_id)  # Alias for get_last_output()
tracker.get_tracker()  # Returns self
```

## Migration from Old System

If you have code using the old `StateTracker` or `ExecutionTracker`:

### No Changes Required
Most code will work without changes due to backward compatibility:
```python
# Old code (still works)
from dipeo.domain.execution.state import StateTracker

tracker = StateTracker()
tracker.initialize_node(node_id)
tracker.transition_to_running(node_id, epoch=0)
# ... etc
```

### Recommended Updates
For new code, use the unified tracker directly:
```python
# New code (recommended)
from dipeo.domain.execution.state import UnifiedStateTracker

tracker = UnifiedStateTracker()
tracker.initialize_node(node_id)
tracker.transition_to_running(node_id, epoch=0)
# ... etc
```

### Removed Features
The following features were removed as they were never used:
- `NodeRuntimeState` (kept for import compatibility only)
- `FlowStatus` enum (token-based flow control is used instead)
- `update_runtime_state()` method (not used by execution engine)
- `reset_for_iteration()` method (use `reset_node()` instead)

## Design Rationale

### Why Unify?

**Previous System:**
- `ExecutionTracker`: Tracked execution history
- `StateTracker`: Wrapped ExecutionTracker, added UI state and iteration limits

**Problems:**
1. Two sources of truth → risk of divergence
2. Leaky abstraction → `get_tracker()` exposed internal tracker
3. Thread safety inconsistency → StateTracker was thread-safe, ExecutionTracker wasn't
4. Maintenance burden → changes required in both classes

**Unified System:**
1. Single source of truth → no divergence possible
2. Encapsulation → all state internal, clean API
3. Consistent thread safety → lock protects all operations
4. Easy maintenance → changes in one place

### Internal Structure

The unified tracker separates concerns internally:

```python
class UnifiedStateTracker:
    # UI State
    self._node_states: dict[NodeID, NodeState]

    # Execution History
    self._execution_records: dict[NodeID, list[NodeExecutionRecord]]
    self._execution_counts: dict[NodeID, int]
    self._last_outputs: dict[NodeID, Envelope]
    self._execution_order: list[NodeID]

    # Iteration Limits
    self._node_iterations_per_epoch: dict[tuple[NodeID, int], int]
    self._max_iterations_per_epoch: int

    # Metadata
    self._node_metadata: dict[NodeID, dict[str, Any]]

    # Thread Safety
    self._lock: threading.Lock
```

## Thread Safety

All public methods are thread-safe:

```python
# Safe concurrent access
def worker(thread_id: int):
    node_id = NodeID(f"node-{thread_id}")
    tracker.initialize_node(node_id)
    for i in range(10):
        tracker.transition_to_running(node_id, epoch=0)
        tracker.transition_to_completed(node_id)
        tracker.reset_node(node_id)

threads = [Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()

# All operations are protected by internal lock
```

## Testing

See `tests/domain/execution/state/test_unified_state_tracker.py` for comprehensive test coverage:
- State transitions (10 tests)
- State queries (6 tests)
- Execution history (8 tests)
- Iteration limits (4 tests)
- Metadata (4 tests)
- Thread safety (3 tests)
- Persistence (2 tests)
- Backward compatibility (3 tests)
- Edge cases (4 tests)

**Total: 44 tests, all passing**

## Performance

- **Thread Safety**: Single lock per tracker (potential contention)
- **Memory**: O(N) where N is number of execution records
- **State Queries**: O(1) for single node, O(N) for all nodes
- **Iteration Lookup**: O(1) per (node, epoch) key

For long-running executions:
- Consider periodic cleanup of old records
- Use persistence for historical data
- Monitor memory usage

## Related Components

- **ExecutionContext** (`context/execution_context.py`): Uses UnifiedStateTracker
- **TokenManager** (`tokens/token_manager.py`): Queries execution counts
- **EventPipeline** (`events/pipeline.py`): Uses states for event building
- **Envelope** (`messaging/envelope.py`): Stores node outputs

## Future Enhancements

1. **Persistence**: Implement ports for database storage
2. **Caching**: Redis-based state cache
3. **Resume**: Load persisted state to resume execution
4. **Streaming**: Stream state updates to UI via WebSocket
5. **Metrics**: Prometheus-style metrics export
6. **Cleanup**: Automatic cleanup of old execution records

## Examples

### Loop with Iteration Limits

```python
tracker = UnifiedStateTracker()
node_id = NodeID("loop-node")
epoch = 0
max_iterations = 10

tracker.initialize_node(node_id)

while True:
    # Check iteration limit
    if not tracker.can_execute_in_loop(node_id, epoch, max_iterations):
        tracker.transition_to_maxiter(node_id)
        break

    # Execute node
    tracker.transition_to_running(node_id, epoch)
    output = execute_node(node)
    envelope = EnvelopeFactory.create(body=output)
    tracker.transition_to_completed(node_id, output=envelope)

    # Check exit condition
    if should_exit(output):
        break

    # Reset for next iteration
    tracker.reset_node(node_id)
```

### Error Handling

```python
tracker.initialize_node(node_id)
tracker.transition_to_running(node_id, epoch=0)

try:
    result = execute_node(node)
    output = EnvelopeFactory.create(body=result)
    tracker.transition_to_completed(node_id, output=output)
except Exception as e:
    tracker.transition_to_failed(node_id, error=str(e))
```

### Execution Summary

```python
# After execution completes
summary = tracker.get_execution_summary()

print(f"Total executions: {summary['total_executions']}")
print(f"Success rate: {summary['success_rate']:.2%}")
print(f"Total duration: {summary['total_duration']:.2f}s")
print(f"Tokens used: {summary['total_tokens']}")
print(f"Execution order: {summary['execution_order']}")
```

## API Reference

### State Transitions
- `initialize_node(node_id)`: Initialize to PENDING
- `transition_to_running(node_id, epoch) -> int`: Start execution
- `transition_to_completed(node_id, output, token_usage)`: Mark success
- `transition_to_failed(node_id, error)`: Mark failed
- `transition_to_maxiter(node_id, output)`: Mark max iterations
- `transition_to_skipped(node_id)`: Mark skipped
- `reset_node(node_id)`: Reset to PENDING

### State Queries
- `get_node_state(node_id) -> NodeState | None`: Get state
- `get_all_node_states() -> dict`: Get all states
- `get_completed_nodes() -> list[NodeID]`: Get completed
- `get_running_nodes() -> list[NodeID]`: Get running
- `get_failed_nodes() -> list[NodeID]`: Get failed
- `has_running_nodes() -> bool`: Check if any running

### Execution History
- `get_execution_count(node_id) -> int`: Cumulative count
- `has_executed(node_id) -> bool`: Check if ever executed
- `get_last_output(node_id) -> Envelope | None`: Last output
- `get_node_result(node_id) -> dict | None`: Result with metadata
- `get_node_execution_history(node_id) -> list`: Full history
- `get_execution_summary() -> dict`: Aggregate metrics
- `get_execution_order() -> list[NodeID]`: Execution sequence

### Iteration Limits
- `can_execute_in_loop(node_id, epoch, max_iteration) -> bool`: Check limit
- `get_iterations_in_epoch(node_id, epoch) -> int`: Count in epoch

### Metadata
- `get_node_metadata(node_id) -> dict`: Get metadata
- `set_node_metadata(node_id, key, value)`: Set metadata

### Persistence
- `load_states(node_states, ...)`: Load persisted state
- `clear_history()`: Clear all history

### Backward Compatibility
- `get_tracker() -> UnifiedStateTracker`: Returns self
- `get_node_execution_count(node_id) -> int`: Alias
- `get_node_output(node_id) -> Envelope | None`: Alias
