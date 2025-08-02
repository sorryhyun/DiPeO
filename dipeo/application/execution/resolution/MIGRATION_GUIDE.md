# Input Resolution Migration Guide

This guide explains how to migrate from the existing input resolution to the new interface-based approach.

## Overview of Changes

The refactoring introduces clear interfaces that separate:
1. **Compile-time resolution** - Static analysis and rule determination
2. **Runtime resolution** - Dynamic value resolution during execution
3. **Node-type strategies** - Encapsulated behavior for different node types
4. **Transformation engine** - Pluggable transformation rules

## Migration Path

### Phase 1: Use Adapters (Current)

The adapters allow existing code to work without changes:

```python
# In your existing code, replace:
from dipeo.application.execution.resolution.input_resolution import TypedInputResolutionService

# With:
from dipeo.application.execution.resolution.adapters import TypedInputResolutionServiceAdapter
service = TypedInputResolutionServiceAdapter()
```

### Phase 2: Gradual Interface Adoption

Start using the new interfaces in new code:

```python
from dipeo.application.execution.resolution.interfaces import (
    RuntimeInputResolver,
    NodeStrategyFactory,
    StandardTransformationEngine,
)

# Create resolver with strategies
resolver = RefactoredRuntimeResolver()
```

### Phase 3: Full Migration

Replace the old implementation entirely:

```python
# Old way
inputs = old_service.resolve_inputs_for_node(
    node_id, node_type, diagram, outputs, exec_counts
)

# New way
from dipeo.application.execution.resolution.refactored_input_resolution import (
    RefactoredInputResolutionService
)

service = RefactoredInputResolutionService()
inputs = service.resolve_inputs_for_node(
    node_id, node_type, diagram, outputs, exec_counts
)
```

## Key Interface Changes

### 1. ExecutionContext

Old: Multiple parameters passed around
```python
def resolve(self, node_id, outputs, exec_counts, memory_config):
    # Use parameters directly
```

New: Unified context object
```python
def resolve(self, node_id, edges, context: ExecutionContext):
    # Access via context
    count = context.get_node_exec_count(node_id)
```

### 2. Node Type Strategies

Old: Embedded special cases
```python
if node_type == NodeType.PERSON_JOB:
    # Special PersonJob logic mixed in
```

New: Separate strategy classes
```python
strategy = NodeStrategyFactory().create_strategy(node)
should_process = strategy.should_process_edge(edge, node, context)
```

### 3. Transformation Rules

Old: Inline transformations
```python
if edge.data_transform and edge.data_transform.get('content_type') == 'object':
    # Transform inline
```

New: Transformation engine
```python
value = transformation_engine.transform(value, edge.data_transform)
```

## Benefits of Migration

1. **Clearer code** - Separation of concerns makes code easier to understand
2. **Better testing** - Each component can be tested in isolation
3. **Extensibility** - Easy to add new node types or transformation rules
4. **Performance** - More work done at compile time
5. **Type safety** - Stronger typing throughout

## Common Migration Issues

### Issue 1: Direct Edge Access
If your code directly accesses edge properties, update to use the interface methods.

### Issue 2: Custom Node Types
Register custom strategies for your node types:
```python
factory = NodeStrategyFactory()
factory.register(MyCustomStrategy())
```

### Issue 3: Custom Transformations
Register custom transformers:
```python
engine = StandardTransformationEngine()
engine.register_transformer("my_rule", MyTransformer())
```

## Testing During Migration

Run the comprehensive test suite to ensure compatibility:
```bash
cd dipeo/application/execution/resolution/tests
pytest -v
```

The tests cover all edge cases and should pass with both old and new implementations.