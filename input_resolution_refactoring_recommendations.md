# Input Resolution Refactoring Recommendations

## Progress Status
- ✓ **Step 1: Refactor Tests** - Completed (59 tests, 98% coverage)
- ☐ Step 2: Extract Interfaces - Pending
- ☐ Step 3: Implement New Components - Pending
- ☐ Step 4: Migration and Cleanup - Pending

## Executive Summary

The current input resolution mechanism in DiPeO is functional but has grown complex with many special cases and scattered responsibilities. This document outlines specific recommendations to improve clarity, maintainability, and extensibility.

## Core Issues Identified

### 1. Separation of Concerns
- Resolution logic is split between compile-time and runtime with unclear boundaries
- Data transformation happens in multiple places
- Special-case handling is embedded in generic code

### 2. Data Structure Proliferation
- Multiple representations of nodes and edges create confusion
- Inconsistent ways to access node outputs
- Intermediate wrapper classes for compatibility

### 3. Complex Special Cases
- PersonJob "first" input handling is deeply embedded
- Content type determination has multiple fallback paths
- Transformation rules come from many sources

## Recommended Refactoring Approach

### Phase 1: Clarify Compile-Time vs Runtime

**1.1 Create Clear Boundaries**
```python
# Compile-time: Structure and rules
class CompileTimeResolver:
    """Resolves static structure and transformation rules"""
    def resolve_connections(self, arrows, nodes) -> list[Connection]
    def determine_transformation_rules(self, connection) -> TransformRules
    
# Runtime: Data flow and execution
class RuntimeInputResolver:
    """Resolves actual input values during execution"""
    def resolve_inputs(self, node_id, edges, outputs) -> dict[str, Any]
```

**1.2 Move All Static Analysis to Compile Time**
- Content type determination
- Transformation rule extraction
- Connection validation
- Special input detection (like "first" inputs)

### Phase 2: Unify Data Structures

**2.1 Single Edge Representation**
```python
@dataclass(frozen=True)
class ExecutableEdge:
    # Identity
    id: str
    source_node_id: NodeID
    target_node_id: NodeID
    
    # Connection details
    source_output: str = "default"
    target_input: str = "default"
    
    # Transformation rules (determined at compile time)
    content_type: ContentType
    transform_rules: TransformRules
    
    # Runtime behavior hints
    is_conditional: bool = False
    requires_first_execution: bool = False
```

**2.2 Consistent Output Protocol**
```python
class NodeOutput:
    """Single way to represent node outputs"""
    value: Any
    outputs: dict[str, Any]  # Named outputs
    metadata: dict[str, Any]
    
    def get_output(self, name: str = "default") -> Any:
        return self.outputs.get(name, self.value)
```

### Phase 3: Extract Special-Case Handlers

**3.1 Strategy Pattern for Node Types**
```python
class NodeTypeStrategy:
    """Base class for node-type-specific behavior"""
    def should_process_edge(self, edge, execution_context) -> bool
    def transform_input(self, value, edge) -> Any

class PersonJobStrategy(NodeTypeStrategy):
    """Handles PersonJob-specific logic"""
    def should_process_edge(self, edge, execution_context) -> bool:
        if execution_context.is_first_execution:
            return edge.requires_first_execution
        return not edge.requires_first_execution
```

**3.2 Rule-Based Transformation System**
```python
class TransformationEngine:
    """Applies transformation rules consistently"""
    def __init__(self):
        self.transformers = {
            'extract_variable': VariableExtractor(),
            'format': Formatter(),
            'content_type_conversion': ContentTypeConverter(),
        }
    
    def transform(self, value: Any, rules: TransformRules) -> Any:
        for rule_type, rule_config in rules.items():
            if rule_type in self.transformers:
                value = self.transformers[rule_type].apply(value, rule_config)
        return value
```

### Phase 4: Simplify the Resolution Pipeline

**4.1 Clear Resolution Flow**
```python
class SimplifiedDiagramCompiler:
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        # 1. Parse structure
        nodes = self.create_executable_nodes(domain_diagram.nodes)
        connections = self.resolve_connections(domain_diagram.arrows)
        
        # 2. Build edges with all rules
        edges = []
        for conn in connections:
            rules = self.build_transformation_rules(conn, nodes)
            edge = self.create_executable_edge(conn, rules)
            edges.append(edge)
        
        # 3. Calculate order
        execution_order = self.calculate_execution_order(nodes, edges)
        
        return ExecutableDiagram(nodes, edges, execution_order)
```

**4.2 Simplified Runtime Resolution**
```python
class SimplifiedInputResolver:
    def resolve_inputs(self, node: ExecutableNode, context: ExecutionContext) -> dict:
        inputs = {}
        
        for edge in context.get_incoming_edges(node.id):
            if self.should_process_edge(edge, node, context):
                value = self.get_edge_value(edge, context)
                transformed = self.apply_transformations(value, edge)
                inputs[edge.target_input] = transformed
        
        return inputs
```

## Implementation Plan

### Step 1: Refactor Tests (Week 1) ✓ COMPLETED
- ✓ Created comprehensive test suite with 59 tests
- ✓ Achieved 98% test coverage (99% for main input_resolution.py)
- ✓ Covered all edge cases including PersonJob first/default inputs
- ✓ Documented expected behavior in tests and INPUT_RESOLUTION_BEHAVIOR.md
- ✓ Created reusable test fixtures for future testing

### Step 2: Extract Interfaces (Week 2)
- Define clear interfaces for each component
- Create adapter classes for backward compatibility
- Gradually migrate to new interfaces

### Step 3: Implement New Components (Week 3-4)
- Build simplified components following new design
- Run parallel with old system for validation
- Migrate one node type at a time

### Step 4: Migration and Cleanup (Week 5)
- Switch to new implementation
- Remove old code
- Update documentation

## Benefits

1. **Clarity**: Clear separation between compile-time and runtime
2. **Maintainability**: Special cases are isolated and explicit
3. **Extensibility**: Easy to add new node types and transformation rules
4. **Performance**: More work done at compile time
5. **Testability**: Smaller, focused components are easier to test

## Risks and Mitigation

1. **Breaking Changes**: Use adapter pattern for backward compatibility
2. **Regression**: Comprehensive test suite before refactoring
3. **Complexity During Migration**: Run old and new systems in parallel

## Conclusion

The proposed refactoring will significantly improve the clarity and maintainability of the input resolution mechanism. By separating concerns, unifying data structures, and extracting special cases, we can create a system that's easier to understand, test, and extend.