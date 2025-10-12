# DiPeO Domain Execution

## Overview

The `dipeo/domain/execution` module defines the **business rules and runtime mechanisms** for diagram execution. It provides token-based flow control, connection rules, data transformation, state management, and input resolution.

This module is organized into focused subdirectories, each handling a specific aspect of execution:

```
dipeo/domain/execution/
├── context/              # Execution context protocol
├── messaging/            # Message envelope system
├── state/                # State tracking (UI visualization + history)
├── tokens/               # Token-based flow control
├── rules/                # Business rules (connections + transforms)
└── resolution/           # Runtime input resolution
```

## Architecture

### Token-Based Flow Control

DiPeO uses **tokens** to control execution flow, not status tracking. When a node completes, it publishes tokens on outgoing edges. A node is ready to execute when it has tokens available per its join policy:

```
┌──────────┐
│  Node A  │──token──> [Edge] ──token──> ┌──────────┐
└──────────┘                              │  Node B  │
                                          └──────────┘
┌──────────┐                              │ JoinPolicy: all
│  Node C  │──token──> [Edge] ──token────┤ (waits for both)
└──────────┘                              └──────────┘
```

Status tracking (`PENDING`, `RUNNING`, `COMPLETED`) is maintained **only for UI visualization**. The execution engine uses token availability to determine readiness.

### Core Principles

1. **Token-Driven Execution**: Readiness is determined by token availability, not status
2. **Immutable Messages**: All data flows through immutable `Envelope` objects
3. **Epoch-Based Loops**: Loop iterations use epochs to track token generations
4. **Separation of Concerns**: State tracking (UI) vs execution flow (tokens) are separate
5. **Pure Business Logic**: No infrastructure dependencies in domain layer

## Core Components

### 1. Token-Based Flow Control (`tokens/`)

Manages token flow through the execution graph.

**Key Types:**
- `Token`: Immutable token with epoch, sequence, and content (Envelope)
- `EdgeRef`: Identifies a specific edge in the diagram
- `JoinPolicy`: Defines readiness criteria (all/any/k_of_n)
- `ConcurrencyPolicy`: Controls concurrent executions (singleton/per-token/bounded)

**TokenManager** (`tokens/token_manager.py:19`):

```python
from dipeo.domain.execution.tokens import TokenManager

# Initialize with diagram
token_mgr = TokenManager(diagram, execution_tracker)

# Publish tokens on node completion
outputs = {"default": envelope}
token_mgr.emit_outputs(node_id, outputs, epoch=0)

# Check if node is ready
is_ready = token_mgr.has_new_inputs(node_id, join_policy="all")

# Consume tokens when executing
inputs = token_mgr.consume_inbound(node_id)
```

**Features:**
- Epoch management for loop iterations
- Join policy evaluation (all/any/k_of_n)
- Branch decision tracking for condition nodes
- Edge mapping for fast lookups
- Token sequencing per edge and epoch

See [tokens/README.md](tokens/README.md) for details.

### 2. Execution Context (`context/`)

The `ExecutionContext` protocol defines the contract for managing runtime state.

**ExecutionContext** (`context/execution_context.py:15`):

```python
from typing import Protocol
from dipeo.domain.execution.context import ExecutionContext

class ExecutionContext(Protocol):
    diagram: ExecutableDiagram
    execution_id: str
    state: StateTracker      # State management
    tokens: TokenManager     # Token flow control

    def current_epoch(self) -> int: ...
    def get_variable(self, name: str) -> Any: ...
    def set_variable(self, name: str, value: Any) -> None: ...
    def consume_inbound(self, node_id: NodeID) -> dict[str, Envelope]: ...
    def emit_outputs_as_tokens(self, node_id: NodeID, outputs: dict[str, Envelope]) -> None: ...
```

The protocol separates concerns:
- `state`: Tracks node states and outputs (UI visualization)
- `tokens`: Manages token flow (execution logic)
- Variables for loop indices and condition results

See [context/README.md](context/README.md) for details.

### 3. State Management (`state/`)

Tracks node execution states and history, primarily for UI visualization and reporting.

**StateTracker** (`state/state_tracker.py:20`):

```python
from dipeo.domain.execution.state import StateTracker

tracker = StateTracker()

# Transition node states (for UI)
tracker.initialize_node(node_id)
tracker.transition_to_running(node_id, epoch=0)
tracker.transition_to_completed(node_id, output=envelope)

# Query state
state = tracker.get_node_state(node_id)  # NodeState(status=COMPLETED)
result = tracker.get_node_result(node_id)
count = tracker.get_node_execution_count(node_id)

# Check iteration limits
can_run = tracker.can_execute_in_loop(node_id, epoch=0, max_iteration=10)
```

**ExecutionTracker** (`state/execution_tracker.py:54`):

```python
# Separates immutable history from mutable runtime state
tracker = ExecutionTracker()

# Track execution lifecycle
exec_num = tracker.start_execution(node_id)
tracker.complete_execution(node_id, CompletionStatus.SUCCESS, output=envelope)

# Query history
count = tracker.get_execution_count(node_id)
has_run = tracker.has_executed(node_id)
records = tracker.get_node_execution_history(node_id)
summary = tracker.get_execution_summary()
```

**Note:** Status tracking is for UI only. Token flow drives execution.

See [state/README.md](state/README.md) for details.

### 4. Message Envelope System (`messaging/`)

All data flows through immutable `Envelope` objects.

**Envelope** (`messaging/envelope.py:21`):

```python
from dipeo.domain.execution.messaging import Envelope, EnvelopeFactory

# Create envelopes
text_env = EnvelopeFactory.create(body="Hello", content_type=ContentType.RAW_TEXT)
json_env = EnvelopeFactory.create(body={"key": "value"}, content_type=ContentType.OBJECT)

# Auto-detect content type
auto_env = EnvelopeFactory.create(body="text")  # Automatically RAW_TEXT

# Access content
text = envelope.as_text()    # Raises if not RAW_TEXT
json = envelope.as_json()    # Raises if not OBJECT
data = envelope.body         # Direct access

# Add metadata (immutable)
with_meta = envelope.with_meta(iteration=5, branch="true")
with_iter = envelope.with_iteration(5)

# Error handling
error_env = EnvelopeFactory.create(body="Error message", error="ValidationError")
has_err = envelope.has_error()
```

**Features:**
- Immutable by design (frozen dataclass)
- Content type safety (RAW_TEXT, OBJECT, BINARY, CONVERSATION_STATE)
- Metadata support (iteration, branch, timestamps)
- Error propagation through envelopes

See [messaging/README.md](messaging/README.md) for details.

### 5. Business Rules (`rules/`)

Defines connection constraints and data transformation rules.

**NodeConnectionRules** (`rules/connection_rules.py:6`):

```python
from dipeo.domain.execution.rules import NodeConnectionRules

# Check if connection is allowed
can_connect = NodeConnectionRules.can_connect(
    source_type=NodeType.PERSON_JOB,
    target_type=NodeType.CONDITION
)  # True

# Get valid targets for a node type
constraints = NodeConnectionRules.get_connection_constraints(NodeType.START)
valid_targets = constraints['can_send_to']  # All except START
valid_sources = constraints['can_receive_from']  # Empty (START has no inputs)
```

**Connection Rules:**
- START nodes cannot receive inputs
- ENDPOINT nodes cannot send outputs
- Nodes cannot connect back to START
- Output-capable nodes: PERSON_JOB, CONDITION, CODE_JOB, API_JOB, START

**DataTransformRules** (`rules/transform_rules.py:11`):

```python
from dipeo.domain.execution.rules import DataTransformRules

# Get type-based transformation
source_node = PersonJobNode(...)
target_node = ConditionNode(...)
transforms = DataTransformRules.get_data_transform(source_node, target_node)
# Returns: {"extract_tool_results": True} if source has tools

# Merge edge-specific and type-based rules
edge_rules = {"custom_rule": "value"}
merged = DataTransformRules.merge_transforms(edge_rules, transforms)
# Edge rules take precedence
```

**Note:** This is a minimal implementation. More complex transformation rules are planned (see Future Enhancements).

See [rules/README.md](rules/README.md) for details.

### 6. Runtime Input Resolution (`resolution/`)

Resolves node inputs during execution by selecting edges, transforming values, and applying defaults.

**Main API** (`resolution/api.py:27`):

```python
from dipeo.domain.execution.resolution import resolve_inputs

# Resolve all inputs for a node
inputs: dict[str, Envelope] = resolve_inputs(node, diagram, ctx)
```

**Resolution Process:**

1. **Edge Selection** (`selectors.py`): Determine which edges are ready
2. **Value Extraction** (`api.py:142`): Extract values from source outputs with content type conversion
3. **Transformation** (`transformation_engine.py`): Apply transformation rules
4. **Special Inputs** (`selectors.py`): Add iteration counts, diagram info
5. **Defaults** (`defaults.py`): Apply default values for missing inputs
6. **Validation**: Ensure required inputs are present

**Components:**
- `api.py` - Main `resolve_inputs()` orchestration
- `transformation_engine.py` - `TransformationEngine` for data transformation
- `node_strategies.py` - Node-type-specific resolution (PersonJob, Condition, Collect)
- `selectors.py` - Edge selection and special input computation
- `defaults.py` - Default value application
- `data_structures.py` - Value objects (InputResolutionContext, ValidationResult)
- `errors.py` - Resolution-specific exceptions

**Features:**
- Smart content type conversion (text ↔ JSON ↔ conversation state)
- Spread/pack modes for data flow
- Node-type-specific strategies
- Special input injection (iteration count, diagram metadata)
- Strict vs loose mode (via `DIPEO_LOOSE_EDGE_VALUE`)

**Example Strategy** (`node_strategies.py`):

```python
from dipeo.domain.execution.resolution import PersonJobNodeStrategy

strategy = PersonJobNodeStrategy()

# Check if inputs are ready
ready = strategy.validate_inputs(node, inputs)

# Apply node-specific transformations
transformed = strategy.transform_inputs(node, inputs)
```

## Usage Examples

### Complete Execution Flow

```python
from dipeo.domain.execution import (
    ExecutionContext,
    Envelope,
    EnvelopeFactory,
    resolve_inputs,
)

# 1. Check token readiness
is_ready = ctx.tokens.has_new_inputs(node_id, join_policy="all")

if is_ready:
    # 2. Transition state (for UI)
    ctx.state.transition_to_running(node_id, epoch=ctx.current_epoch())

    # 3. Consume tokens
    token_inputs = ctx.consume_inbound(node_id)

    # 4. Resolve actual inputs
    resolved_inputs = resolve_inputs(node, diagram, ctx)

    # 5. Execute node (handler logic)
    result = execute_node(node, resolved_inputs)

    # 6. Create output envelope
    output = EnvelopeFactory.create(body=result, node_id=node_id)

    # 7. Update state (for UI)
    ctx.state.transition_to_completed(node_id, output=output)

    # 8. Publish tokens on outgoing edges
    ctx.emit_outputs_as_tokens(node_id, {"default": output})
```

### Loop Execution with Epochs

```python
# Enter loop - new epoch
epoch = ctx.tokens.begin_epoch()

# Execute loop body nodes
while has_work:
    for node_id in loop_body:
        if ctx.tokens.has_new_inputs(node_id, epoch=epoch):
            # Execute node...
            ctx.tokens.emit_outputs(node_id, outputs, epoch=epoch)

    # Check iteration limit
    if not ctx.state.can_execute_in_loop(node_id, epoch, max_iteration=10):
        ctx.state.transition_to_maxiter(node_id)
        break
```

### Validate Connections

```python
from dipeo.domain.execution.rules import NodeConnectionRules

# Check connection validity at compile time
source_type = NodeType.PERSON_JOB
target_type = NodeType.ENDPOINT

if NodeConnectionRules.can_connect(source_type, target_type):
    print("Connection allowed")
else:
    raise ValueError("Invalid connection")
```

## Testing

Unit tests should focus on:

1. **Token Flow**: Token publishing, consumption, and readiness checks
2. **Join Policies**: All/any/k_of_n semantics
3. **Connection Rules**: Valid/invalid connections between node types
4. **Envelope Immutability**: Metadata operations return new instances
5. **Resolution Logic**: Edge selection, transformation, defaults

Example tests:

```python
def test_token_flow():
    """Test basic token publishing and consumption"""
    token_mgr = TokenManager(diagram)

    # Publish token
    envelope = EnvelopeFactory.create(body="data")
    edge = EdgeRef(source_node_id="A", target_node_id="B", ...)
    token = token_mgr.publish_token(edge, envelope)

    # Check readiness
    assert token_mgr.has_new_inputs("B", join_policy="all")

    # Consume
    inputs = token_mgr.consume_inbound("B")
    assert "default" in inputs

def test_connection_rules():
    """Test connection validation"""
    # Valid
    assert NodeConnectionRules.can_connect(NodeType.START, NodeType.PERSON_JOB)

    # Invalid
    assert not NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.START)
    assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.PERSON_JOB)
```

## Performance Considerations

- **Edge Mapping**: TokenManager pre-builds edge maps for O(1) lookups
- **Immutable Messages**: Envelopes are immutable, enabling safe sharing
- **Thread Safety**: StateTracker uses locks for concurrent access
- **Lazy Evaluation**: Inputs resolved only when node executes
- **Epoch Isolation**: Tokens are keyed by (edge, epoch, seq) for isolation

## Dependencies

**Internal:**
- `dipeo.diagram_generated` - Generated node types and enums
- `dipeo.domain.diagram.models` - Diagram models (ExecutableDiagram, ExecutableNode)
- `dipeo.config.base_logger` - Logging

**External:**
- Python 3.13+ standard library
- `dataclasses` - Immutable data structures
- `typing` - Type hints and protocols

## Future Enhancements

The following features are **planned but not yet implemented**:

1. **Rule Registry** (Task 31): Dynamic rule loading and registration
2. **Advanced Transformation Rules**: Complex transformation pipelines with TransformRule dataclass
3. **TransformationType Enum**: Typed transformation operations (extract/format/aggregate/filter/map)
4. **Data Flow Validation**: Type compatibility checking between nodes
5. **Rule Composition**: Combine multiple rules with AND/OR logic
6. **Retry Policies**: Configurable retry logic with exponential backoff
7. **Rule Versioning**: Support different rule versions per diagram
8. **Machine Learning Rules**: Learn rules from execution history

## Related Documentation

- [Overall Architecture](../../docs/architecture/overall_architecture.md) - System-wide architecture
- [Diagram Compilation](../../docs/architecture/diagram-compilation.md) - Compile-time processing
- [Execution Engine](../../application/execution/README.md) - Application-layer orchestration
- [Node Handlers](../../application/execution/handlers/README.md) - Node-specific execution logic
