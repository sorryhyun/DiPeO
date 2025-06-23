# Simplified Execution State Model

## Overview

The execution domain has been refactored to use a simplified state model that provides a cleaner, more consistent approach to tracking diagram execution. This document describes the key components and how to use them.

## Core Types

### ExecutionState
The main state object that tracks the entire execution:

```python
class ExecutionState:
    id: ExecutionID
    status: ExecutionStatus  # STARTED, RUNNING, COMPLETED, FAILED, ABORTED
    diagram_id: Optional[DiagramID]
    started_at: str
    ended_at: Optional[str]
    node_states: Dict[str, NodeState]  # Node execution tracking
    node_outputs: Dict[str, NodeOutput]  # Node outputs
    token_usage: TokenUsage
    error: Optional[str]
    variables: Dict[str, Any]
    duration_seconds: Optional[float]
    is_active: Optional[bool]
```

### NodeState
Tracks individual node execution status:

```python
class NodeState:
    status: NodeExecutionStatus  # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
    started_at: Optional[str]
    ended_at: Optional[str]
    error: Optional[str]
    skip_reason: Optional[str]
    token_usage: Optional[TokenUsage]
```

### NodeOutput
Unified output format for all node types:

```python
class NodeOutput:
    value: Dict[str, Any]  # The actual output data
    metadata: Dict[str, Any]  # Additional metadata (tokens, errors, etc.)
```

## Key Changes from Legacy Model

1. **Removed Legacy Types**: `NodeResult` and `ExecutionResult` have been removed
2. **Unified Output Format**: All nodes now use `NodeOutput` with a consistent `value` property
3. **Simplified State Storage**: Direct dictionaries for node states and outputs
4. **Cleaner GraphQL Serialization**: Simplified serialization using `model_dump()`

## Usage Examples

### Creating Node Output

```python
from dipeo_server.domains.execution.handlers import create_node_output

# Simple output
output = create_node_output(
    value={'default': 'Hello World'},
    metadata={'tokens_used': 10}
)

# Multiple outputs
output = create_node_output(
    value={
        'success': result_data,
        'error': None
    },
    metadata={'execution_time': 1.5}
)
```

### Writing Node Handlers

```python
from dipeo_server.domains.execution.handlers import node_handler, create_node_output

@node_handler("MyNodeType")
async def execute_my_node(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    # Update status
    await ctx.state_store.update_node_status(
        ctx.execution_id, node.id, NodeExecutionStatus.RUNNING
    )
    
    # Process the node
    result = await process_node_logic(node, ctx)
    
    # Create output
    output = create_node_output(
        value={'default': result},
        metadata={'processed': True}
    )
    
    # Update completion status
    await ctx.state_store.update_node_status(
        ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output
    )
    
    return output
```

### Accessing Node Outputs

```python
# In a handler, get output from a previous node
from_output = ctx.get_node_output(source_node_id)
if from_output:
    # Access the value property
    data = from_output.value.get('default')
```

## State Management

The `StateStore` class handles persistence of execution state:

- Stores state in SQLite with JSON serialization
- Provides async methods for creating and updating executions
- Automatically tracks node status changes
- Maintains execution history

## GraphQL Integration

The execution state is exposed through GraphQL with:

- `ExecutionStateType`: Main execution state with JSON fields for dynamic data
- Real-time subscriptions for execution updates
- Mutations for controlling execution (pause, resume, abort)

## Best Practices

1. Always use `create_node_output()` helper to create outputs
2. Access output data through the `value` property
3. Use metadata for non-output data (errors, tokens, etc.)
4. Update node status before and after execution
5. Handle errors gracefully with proper error outputs