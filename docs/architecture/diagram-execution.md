# Diagram Execution Architecture

## Overview

DiPeO uses a **token-based execution model** where data flows through the diagram as tokens along edges between nodes. This document describes the core execution behaviors and architecture.

## Core Concepts

### Tokens
Tokens are the fundamental unit of data flow in DiPeO:
- Each token carries an `Envelope` containing typed data and metadata
- Tokens are identified by `(edge, epoch, sequence_number)`
- Tokens flow along edges from source node outputs to target node inputs
- Nodes execute when they have sufficient tokens on their input edges

### Epochs
Epochs track execution generations:
- Each diagram execution starts at epoch 0
- Loop controllers increment epochs for iterations
- Nodes track execution count per epoch (for max_iteration enforcement)
- Tokens are scoped to epochs to prevent cross-iteration interference

### Envelopes
Envelopes provide typed communication between nodes:
- Contain the actual data payload (`body`)
- Include metadata (execution time, token usage, etc.)
- Support multiple representations (text, JSON, binary)
- Track lineage via `produced_by` and `trace_id`

## Join Policies

Join policies determine when a node has sufficient inputs to execute:

### ALL (Default)
- Node requires tokens on **all** non-conditional input edges
- Most common for sequential processing
- Ensures all dependencies are met before execution

### ANY
- Node requires token on **at least one** input edge
- Used for condition nodes and parallel branches
- Allows flexible execution patterns

### K_OF_N
- Node requires tokens on **at least K** input edges
- Useful for partial consensus or quorum patterns
- Configured via node properties

## Condition Nodes

Condition nodes implement branching logic:

### Branch Selection
1. Condition evaluates to true/false
2. Token published only on active branch (`condtrue` or `condfalse`)
3. Branch decision stored in context for downstream reference
4. Non-selected branches receive no tokens (natural flow control)

#### Skippable Conditions
- Marked with `skippable: true` property
- Incoming edges from skippable conditions are **not required** for downstream nodes
- Allows optional branching without blocking execution
- Example: Optional validation that shouldn't prevent main flow

**Important Edge Case**: When a skippable condition becomes the only remaining dependency (e.g., after START nodes have executed), it should become required to prevent deadlock

## START Node Behavior

### Single Execution
- START nodes execute exactly once at the beginning of diagram execution
- They publish tokens only during their single execution
- After execution, START nodes do not produce new tokens even in loop scenarios

### Interaction with Loops
When a node has incoming edges from both START and loop-back edges (e.g., from a condition):

1. **First iteration**: Node can execute with just the START token
2. **Subsequent iterations**: Node must receive tokens from the loop-back edge only

**Known Issue**: Currently, there's a deadlock scenario when:
- A node has edges from both START and a skippable condition
- After START executes, the skippable condition becomes the only dependency
- The condition hasn't executed yet, creating a circular dependency

**Proposed Solution**: 
- Track whether a node has already consumed tokens from START
- Only ignore START edges after the target node has executed at least once
- Make skippable conditions required when they become the sole dependency

## Loop Control

### PersonJobNode Iterations
- `max_iteration` property limits executions per node
- Counter tracked per `(node_id, epoch)` pair
- Node transitions to `MAXITER_REACHED` when limit hit
- Downstream nodes can detect via `detect_max_iterations` condition

### Loop Flow
```yaml
# Example loop structure
start -> person_job -> condition -> person_job (loop back)
                    \-> endpoint (exit)
```

1. PersonJobNode executes up to `max_iteration` times
2. Condition checks if max reached (`detect_max_iterations`)
3. On false: Token sent back to PersonJobNode
4. On true: Token sent to exit path
5. Loop naturally terminates when no new tokens arrive

## Execution Flow

### Node Execution Sequence
1. **Token Arrival**: Token published on edge to node
2. **Readiness Check**: Scheduler checks join policy
3. **Consumption**: Node consumes all available input tokens
4. **Execution**: Handler processes inputs
5. **Output**: Results wrapped in Envelope
6. **Token Emission**: Output tokens published on outgoing edges

### Parallel Execution
- Multiple nodes can execute concurrently if ready
- Engine manages parallelism with semaphores
- Default max concurrent: 20 nodes
- Each node execution is independent

### Handler Pattern
```python
class NodeHandler:
    def consume_token_inputs(request, inputs):
        # Get tokens from incoming edges
        return context.consume_inbound(node_id)
    
    def execute_with_envelopes(request, inputs):
        # Process inputs, return Envelope
        return EnvelopeFactory.json(result)
    
    # Engine emits outputs as tokens automatically
```

## State Management

### Node States (UI Only)
- `PENDING`: Not yet executed
- `RUNNING`: Currently executing
- `COMPLETED`: Successfully finished
- `FAILED`: Execution error
- `MAXITER_REACHED`: Hit iteration limit
- `SKIPPED`: Not executed (conditional branch)

**Important**: States are for UI visualization only. Token presence drives actual execution.

### Execution Context Responsibilities
- **Token operations**: Publish, consume, track tokens
- **State transitions**: Update node states for UI
- **Event emission**: Notify subscribers of progress
- **Service access**: Provide handlers with dependencies

## Key Principles

1. **Token-Driven**: Execution is driven entirely by token flow
2. **Stateless Nodes**: Nodes don't maintain state between executions
3. **Epoch Isolation**: Tokens from different epochs don't interfere
4. **Natural Flow Control**: Branching via selective token emission
5. **Implicit Synchronization**: Join policies handle coordination

## Example Execution Trace

### Successful Loop Execution
```
Epoch 0:
1. Start node executes -> publishes token to PersonJob
2. PersonJob (iteration 1) -> publishes token to Condition
3. Condition evaluates false -> publishes token back to PersonJob
4. PersonJob (iteration 2) -> publishes token to Condition
5. Condition evaluates false -> publishes token back to PersonJob
6. PersonJob (iteration 3) -> publishes token to Condition
7. Condition detects max_iterations -> publishes token to Ask
8. Ask node executes -> publishes token to Endpoint
9. Endpoint saves result -> execution complete
```

### Problematic Scenario (Current Issue)
When PersonJob has edges from both START and skippable condition:
```
start -> person_job <- condition (skippable, loop-back)
             |
             v
         condition
```

**What happens**:
1. START executes, publishes token to PersonJob
2. PersonJob executes (consumes START token)
3. PersonJob publishes token to Condition
4. Condition evaluates false, should publish token back to PersonJob
5. **DEADLOCK**: PersonJob now requires token from Condition (START is ignored after execution)
   - But Condition edge was "skippable" initially
   - System makes it required since it's the only edge left
   - However, no token emission happens from Condition to PersonJob
```

## Benefits of Token-Based Architecture

### Simplicity
- Single mechanism (tokens) drives all execution
- No complex state machines or status tracking
- Natural handling of loops and branches

### Flexibility
- Easy to add new join policies
- Condition nodes naturally implement branching
- Loops work without special handling

### Performance
- Parallel execution when tokens available
- No global locks or synchronization
- Efficient ready-node detection

### Debugging
- Token flow is traceable
- Clear causality chain
- Epoch tracking shows iteration history

## Future Enhancements

### Immediate Priority
- **Fix START/skippable condition deadlock**: Resolve the issue where skippable conditions become required after START execution but don't emit tokens properly
- **Condition token emission verification**: Ensure condition nodes properly emit tokens on their selected branches (condtrue/condfalse)

### Planned
- Token TTL for automatic cleanup
- Token priorities for execution ordering
- Stream processing with windowed tokens
- Token transformers for edge-level processing

### Under Consideration
- Token replay for debugging
- Token persistence for fault tolerance
- Distributed token passing for scale-out
- Token-based backpressure control