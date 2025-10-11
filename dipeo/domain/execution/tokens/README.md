# Token-Based Flow Control

## Overview

DiPeO uses **token-based flow control** to drive execution. When a node completes, it publishes tokens on outgoing edges. A downstream node is ready to execute when it has tokens available per its join policy.

**Key Principle:** Tokens, not status, determine execution readiness.

## Why Tokens?

**Problem with Status-Based Execution:**
```python
# Status-based (fragile)
if node_status == "COMPLETED" and dependencies_satisfied():
    execute_node()
```

Issues:
- Race conditions (status changes mid-check)
- Unclear semantics (what if status is COMPLETED but already consumed?)
- No iteration support (status is global, not per-iteration)

**Solution: Token-Based Flow:**
```python
# Token-based (robust)
if has_new_tokens(node):
    tokens = consume_tokens(node)
    execute_node(tokens)
    emit_tokens(outputs)
```

Benefits:
- **Explicit data flow**: Tokens carry data (Envelopes)
- **Iteration support**: Tokens are epoch-scoped
- **Atomicity**: Consume and emit are atomic operations
- **Deterministic**: Clear semantics for readiness

## Core Concepts

### Token

**Location:** `dipeo/domain/execution/tokens/token_types.py:25`

```python
@dataclass(frozen=True)
class Token:
    epoch: int                    # Loop iteration (0 = initial)
    seq: int                      # Sequence number on this edge
    content: Envelope             # The actual data
    ts_ns: int                    # Timestamp (nanoseconds)
    meta: dict[str, Any]          # Additional metadata
    token_id: str                 # Unique ID (UUID)

    def with_meta(self, **kwargs) -> Token:
        """Add metadata (returns new token)."""
```

A token represents a single data item flowing along an edge.

**Key fields:**
- `epoch`: Which loop iteration (0 for non-loop)
- `seq`: Sequence number (1, 2, 3, ...) for this edge and epoch
- `content`: The Envelope carrying the actual data
- `token_id`: Unique identifier for tracing

### EdgeRef

**Location:** `dipeo/domain/execution/tokens/token_types.py:12`

```python
@dataclass(frozen=True)
class EdgeRef:
    source_node_id: NodeID
    source_output: str | None     # "default", "condtrue", "condfalse"
    target_node_id: NodeID
    target_input: str | None      # "default", "input2", etc.

    def __hash__(self): ...
```

Identifies a specific edge in the diagram. Used as a key for token storage.

### JoinPolicy

**Location:** `dipeo/domain/execution/tokens/token_types.py:46`

```python
@dataclass
class JoinPolicy:
    policy_type: str = "all"      # "all", "any", "k_of_n"
    k: int | None = None          # For k_of_n

    def is_ready(self, available_edges: set[EdgeRef], new_token_edges: set[EdgeRef]) -> bool:
        """Check if join condition is satisfied."""
```

Defines when a node is ready based on available tokens.

**Policy types:**
- `all`: All incoming edges must have new tokens
- `any`: At least one incoming edge has new tokens
- `k_of_n`: At least k edges have new tokens

### ConcurrencyPolicy

**Location:** `dipeo/domain/execution/tokens/token_types.py:61`

```python
@dataclass
class ConcurrencyPolicy:
    mode: str = "singleton"       # "singleton", "per-token", "bounded"
    max_concurrent: int = 1

    def can_arm(self, current_running: int) -> bool:
        """Check if node can start given current running count."""
```

Controls concurrent executions of the same node.

**Modes:**
- `singleton`: Only one instance at a time
- `per-token`: One instance per token (parallel processing)
- `bounded`: Up to max_concurrent instances

**Note:** Currently not enforced by execution engine (planned feature).

## TokenManager

**Location:** `dipeo/domain/execution/tokens/token_manager.py:19`

Manages token flow through the execution graph.

### Initialization

```python
from dipeo.domain.execution.tokens import TokenManager

token_mgr = TokenManager(diagram, execution_tracker)
```

**Arguments:**
- `diagram`: ExecutableDiagram to manage tokens for
- `execution_tracker`: Optional ExecutionTracker for checking execution counts

**On init:**
- Builds edge maps (`_in_edges`, `_out_edges`) for O(1) lookups
- Initializes epoch to 0
- Sets up token storage

### Epoch Management

Epochs track loop iterations.

**current_epoch() -> int**
```python
epoch = token_mgr.current_epoch()  # 0
```

**begin_epoch() -> int**
```python
# Enter loop - new epoch
epoch = token_mgr.begin_epoch()  # 1
```

Use epochs to isolate loop iterations:
```python
# Epoch 0: Initial execution
execute_nodes(epoch=0)

# Epoch 1: First loop iteration
epoch = token_mgr.begin_epoch()
execute_nodes(epoch=1)

# Epoch 2: Second loop iteration
epoch = token_mgr.begin_epoch()
execute_nodes(epoch=2)
```

### Publishing Tokens

**publish_token(edge: EdgeRef, payload: Envelope, epoch: int | None = None) -> Token**

Publish a single token on an edge:
```python
edge = EdgeRef(
    source_node_id="node-a",
    source_output="default",
    target_node_id="node-b",
    target_input="default"
)

envelope = EnvelopeFactory.create(body="data")
token = token_mgr.publish_token(edge, envelope, epoch=0)

# Token(epoch=0, seq=1, content=envelope, ...)
```

**emit_outputs(node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None) -> None**

Emit outputs on all outgoing edges:
```python
outputs = {
    "default": EnvelopeFactory.create(body="result"),
    "error": None  # Skipped
}

token_mgr.emit_outputs(node_id="node-a", outputs=outputs, epoch=0)

# Publishes token on each outgoing edge with matching source_output
```

**Special handling for condition nodes:**
```python
# Condition node emits on ONE branch
outputs = {
    "condtrue": EnvelopeFactory.create(body=True)
    # OR "condfalse"
}

token_mgr.emit_outputs(node_id="condition-1", outputs=outputs)

# Tracks branch decision for later filtering
assert token_mgr.get_branch_decision("condition-1") == "condtrue"
```

### Consuming Tokens

**consume_inbound(node_id: NodeID, epoch: int | None = None) -> dict[str, Envelope]**

Atomically consume tokens from all incoming edges:
```python
inputs = token_mgr.consume_inbound(node_id="node-b", epoch=0)

# inputs = {
#     "default": Envelope(body="data"),
#     "input2": Envelope(body={"key": "value"})
# }
```

**Atomicity:** Each edge's latest token is consumed exactly once per call.

**Port mapping:** Tokens are keyed by `edge.target_input` (e.g., "default", "input2").

### Checking Readiness

**has_new_inputs(node_id: NodeID, epoch: int | None = None, join_policy: str = "all") -> bool**

Check if a node has new tokens to process:
```python
# Check if ready with "all" policy
is_ready = token_mgr.has_new_inputs(
    node_id="node-b",
    epoch=0,
    join_policy="all"
)

# Check with "any" policy
is_ready = token_mgr.has_new_inputs(
    node_id="node-b",
    epoch=0,
    join_policy="any"
)
```

**Join policy semantics:**
- `"all"`: All incoming edges must have unconsumed tokens
- `"any"`: At least one incoming edge has unconsumed tokens

**Special cases:**
1. **No incoming edges**: Returns True (e.g., START node)
2. **START node edges**: Only checked on first execution (exec_count == 0)
3. **Condition branches**: Only checks tokens on the taken branch
4. **Skippable conditions**: Falls back to alternative edges if main condition skippable

### Branch Decisions

**get_branch_decision(node_id: NodeID) -> str | None**

Get the branch taken by a condition node:
```python
decision = token_mgr.get_branch_decision("condition-1")
# Returns: "condtrue" or "condfalse" or None
```

Used internally to filter edges when checking readiness.

## Token Storage

Tokens are stored in internal dictionaries:

```python
# Sequence counter per (edge, epoch)
_edge_seq: dict[tuple[EdgeRef, int], int]

# Token storage: (edge, epoch, seq) -> Envelope
_edge_tokens: dict[tuple[EdgeRef, int, int], Envelope]

# Last consumed sequence: (node_id, edge, epoch) -> seq
_last_consumed: dict[tuple[NodeID, EdgeRef, int], int]
```

**Example:**
```python
# Edge A->B, epoch 0
# publish_token() increments seq: 1, 2, 3, ...
_edge_seq[(EdgeRef(A, B), 0)] = 3

# Store tokens
_edge_tokens[(EdgeRef(A, B), 0, 1)] = envelope1
_edge_tokens[(EdgeRef(A, B), 0, 2)] = envelope2
_edge_tokens[(EdgeRef(A, B), 0, 3)] = envelope3

# B consumes: last_consumed = 3
_last_consumed[(B, EdgeRef(A, B), 0)] = 3

# has_new_inputs checks: seq (3) > last_consumed (3) ? No
```

## Usage Patterns

### Basic Execution Flow

```python
token_mgr = TokenManager(diagram)

# 1. Check readiness
if token_mgr.has_new_inputs(node_id):

    # 2. Consume tokens
    token_inputs = token_mgr.consume_inbound(node_id)

    # 3. Execute node
    result = execute_node(node, token_inputs)

    # 4. Create output
    output = EnvelopeFactory.create(body=result)

    # 5. Emit tokens
    token_mgr.emit_outputs(node_id, {"default": output})
```

### Loop Execution

```python
# Initial execution (epoch 0)
execute_all_nodes(epoch=0)

# Enter loop
max_iterations = 10
for i in range(max_iterations):
    epoch = token_mgr.begin_epoch()

    # Execute loop body
    for node_id in loop_body:
        if token_mgr.has_new_inputs(node_id, epoch=epoch):
            inputs = token_mgr.consume_inbound(node_id, epoch=epoch)
            result = execute_node(node, inputs)
            output = EnvelopeFactory.create(body=result).with_iteration(i)
            token_mgr.emit_outputs(node_id, {"default": output}, epoch=epoch)

    # Check exit condition
    if should_exit():
        break
```

### Condition Nodes

```python
# Execute condition
condition_result = evaluate_condition(node, inputs)

# Emit on correct branch
if condition_result:
    outputs = {"condtrue": EnvelopeFactory.create(body=True)}
else:
    outputs = {"condfalse": EnvelopeFactory.create(body=False)}

token_mgr.emit_outputs(node_id, outputs)

# Downstream nodes only execute on taken branch
if token_mgr.has_new_inputs(true_branch_node):
    # Only true if condition was true
    execute_node(true_branch_node)
```

### Join Policies

```python
# Node with multiple inputs
node_with_join = diagram.get_node("join-node")

# All inputs must be ready
if token_mgr.has_new_inputs("join-node", join_policy="all"):
    inputs = token_mgr.consume_inbound("join-node")
    # inputs has data from ALL incoming edges

# Any input is sufficient
if token_mgr.has_new_inputs("any-node", join_policy="any"):
    inputs = token_mgr.consume_inbound("any-node")
    # inputs has data from at least ONE edge
```

## Special Cases

### START Node

START nodes are special:
- No incoming edges
- Always ready on first execution
- After first execution, ignored (START only fires once)

Implementation:
```python
# In has_new_inputs()
if source_node.type == NodeType.START:
    if node_exec_count > 0:
        continue  # Skip START edge after first execution
```

### Skippable Conditions

Condition nodes can be marked as "skippable":
```python
condition_node.skippable = True
```

When skippable:
- If the only incoming edges are from skippable conditions, treat as ready
- Allows execution even if condition hasn't fired

Use case: Optional branches that shouldn't block downstream nodes.

### Multiple Condition Inputs

When a node has multiple incoming edges from different conditions:
```python
# Node B has inputs from Condition A and Condition C
# If only ONE condition fires, B still waits for all

# Solution: Mark conditions as skippable
condition_a.skippable = True
condition_c.skippable = True

# Now B can execute if any condition fires
```

## Design Rationale

### Why Token-Based?

**Alternative 1: Status-based**
```python
if all(get_status(dep) == "COMPLETED" for dep in dependencies):
    execute_node()
```

Problems:
- Race conditions (status can change)
- No iteration support (status is global)
- Unclear consumption semantics

**Alternative 2: Event-based**
```python
on_node_completed(node_id):
    for dep in dependents:
        if all_dependencies_met(dep):
            execute_node(dep)
```

Problems:
- Push-based (harder to control)
- No backpressure
- Complex error handling

**Token-based (chosen):**
- Pull-based (node consumes when ready)
- Epoch-scoped (iteration support)
- Atomic consume (clear semantics)
- Backpressure (tokens accumulate if not consumed)

### Why Store Envelopes in Tokens?

Tokens carry Envelopes (not raw data) for:
- Type safety (ContentType)
- Metadata (iteration, branch)
- Error propagation
- Tracing (trace_id)

### Why Separate epoch and seq?

**Epoch:** Loop iteration
**Seq:** Sequence within epoch

This allows:
- Multiple tokens per edge per epoch
- Clear iteration boundaries
- Independent consumption per epoch

```python
# Edge A->B, epoch 0: seq 1, 2, 3
# Edge A->B, epoch 1: seq 1, 2, 3 (reset)

# B can consume from both epochs independently
inputs_0 = consume_inbound(epoch=0)  # Gets seq 3 from epoch 0
inputs_1 = consume_inbound(epoch=1)  # Gets seq 3 from epoch 1
```

## Performance Considerations

- **Edge Maps**: Pre-built on init (O(E) time, O(1) lookups)
- **Token Storage**: In-memory dict (grows with executions)
- **Sequence Tracking**: O(1) increment per token
- **Consumption**: O(edges) per consume call
- **Readiness Check**: O(edges) per check

For long-running executions:
- Tokens accumulate in memory (no cleanup)
- Consider periodic cleanup of old epochs
- Future: Disk-based token storage

## Testing

```python
def test_basic_token_flow():
    token_mgr = TokenManager(diagram)

    # Publish token
    edge = EdgeRef(source_node_id="A", target_node_id="B", ...)
    envelope = EnvelopeFactory.create(body="data")
    token = token_mgr.publish_token(edge, envelope)

    # Check readiness
    assert token_mgr.has_new_inputs("B", join_policy="all")

    # Consume
    inputs = token_mgr.consume_inbound("B")
    assert "default" in inputs
    assert inputs["default"].body == "data"

    # Consumed - no longer ready
    assert not token_mgr.has_new_inputs("B", join_policy="all")

def test_join_policy():
    # Node with 2 inputs
    edge1 = EdgeRef(source_node_id="A", target_node_id="C", ...)
    edge2 = EdgeRef(source_node_id="B", target_node_id="C", ...)

    # Publish on one edge
    token_mgr.publish_token(edge1, envelope)

    # "any" is ready
    assert token_mgr.has_new_inputs("C", join_policy="any")

    # "all" is NOT ready (missing edge2)
    assert not token_mgr.has_new_inputs("C", join_policy="all")

    # Publish on second edge
    token_mgr.publish_token(edge2, envelope)

    # "all" is now ready
    assert token_mgr.has_new_inputs("C", join_policy="all")
```

## Related Components

- **ExecutionContext** (`context/execution_context.py`): Uses TokenManager
- **Envelope** (`messaging/envelope.py`): Token payload
- **StateTracker** (`state/state_tracker.py`): Parallel state tracking (for UI)

## Future Enhancements

1. **Backpressure**: Limit token accumulation per edge
2. **Priority**: Priority tokens for urgent execution
3. **Expiration**: Time-to-live for tokens
4. **Persistent Tokens**: Store tokens on disk for large graphs
5. **Token Metrics**: Prometheus-style metrics (token rate, latency)
6. **Concurrency Policies**: Enforce ConcurrencyPolicy in execution engine
