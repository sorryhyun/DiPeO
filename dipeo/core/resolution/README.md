# Input Resolution Interfaces

This package contains the interface definitions for the refactored input resolution system in DiPeO.

## Architecture Overview

The interfaces establish clear boundaries between different aspects of input resolution:

```
┌─────────────────────────────────────────────────────────┐
│                    Compile Time                         │
├─────────────────────────────────────────────────────────┤
│  CompileTimeResolver                                    │
│  - resolve_connections()                                │
│  - determine_transformation_rules()                     │
│  - validate_connection()                                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  ExecutableEdgeV2                       │
│  - Identity (id, source, target)                        │
│  - Connection details (inputs/outputs)                  │
│  - Transform rules (compile-time determined)            │
│  - Runtime hints (conditional, first_execution)         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     Runtime                             │
├─────────────────────────────────────────────────────────┤
│  RuntimeInputResolver                                   │
│  - resolve_inputs()                                     │
│  - should_process_edge()                                │
│  - get_edge_value()                                     │
│  - apply_transformations()                              │
└─────────────────────────────────────────────────────────┘
```

## Key Interfaces

### 1. Resolvers (`resolvers.py`)

- **CompileTimeResolver**: Handles static analysis during diagram compilation
- **RuntimeInputResolver**: Resolves actual values during execution
- **ExecutionContext**: Provides runtime state information

### 2. Data Structures (`data_structures.py`)

- **ExecutableEdgeV2**: Enhanced edge with all resolution information
- **NodeOutputProtocolV2**: Consistent interface for node outputs
- **StandardNodeOutput**: Default implementation of output protocol

### 3. Node Strategies (`node_strategies.py`)

- **NodeTypeStrategy**: Base class for node-specific behavior
- **PersonJobStrategy**: Handles PersonJob "first" input logic
- **NodeStrategyFactory**: Creates appropriate strategies

### 4. Transformation Engine (`transformation_engine.py`)

- **TransformationEngine**: Applies transformation rules
- **TransformationRule**: Individual transformation implementations
- **StandardTransformationEngine**: Default engine with built-in rules

## Usage Examples

### Creating a Custom Node Strategy

```python
from dipeo.diagram_generated import NodeType
from .node_strategies import NodeTypeStrategy

class MyCustomNodeStrategy(NodeTypeStrategy):
    @property
    def node_type(self) -> NodeType:
        return NodeType.MY_CUSTOM
    
    def should_process_edge(self, edge, node, context, has_special_inputs):
        # Custom logic for edge processing
        return True
    
    def transform_input(self, value, edge, context):
        # Custom transformation logic
        return value

# Register the strategy
factory = NodeStrategyFactory()
factory.register(MyCustomNodeStrategy())
```

### Adding a Custom Transformation

```python
from .transformation_engine import TransformationRule

class MyTransformer:
    @property
    def rule_type(self) -> str:
        return "my_transform"
    
    def can_apply(self, value, config):
        return isinstance(value, dict)
    
    def apply(self, value, config):
        # Transform the value
        return transformed_value

# Register with engine
engine = StandardTransformationEngine()
engine.register_transformer("my_transform", MyTransformer())
```

## Design Principles

1. **Separation of Concerns**: Compile-time vs runtime logic is clearly separated
2. **Open/Closed Principle**: Easy to extend with new strategies and transformations
3. **Interface Segregation**: Small, focused interfaces for specific responsibilities
4. **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations

## Benefits

- **Clarity**: Each component has a single, well-defined responsibility
- **Testability**: Components can be tested in isolation with mocks
- **Extensibility**: New node types and transformations are easy to add
- **Performance**: More analysis done at compile time
- **Maintainability**: Special cases are isolated in strategies

