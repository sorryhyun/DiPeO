# DiPeO Domain Execution Rules

## Overview

The `dipeo/domain/execution` module defines the **business rules and logic** for diagram execution flow. It establishes connection constraints between node types, data transformation rules, and dynamic execution order calculation - forming the domain-level execution semantics independent of infrastructure.

## Architecture

### Rule-Based System

```
┌─────────────────────────────────┐
│     Execution Domain Rules      │
├─────────────────────────────────┤
│  Connection Rules               │ ◄── Which nodes can connect
│  Transformation Rules           │ ◄── How data flows between nodes  
│  Dynamic Order Calculation      │ ◄── Runtime execution scheduling
└─────────────────────────────────┘
           │
    Used by ▼
┌─────────────────────────────────┐
│   Compilation (Validation)      │
│   Execution Engine (Runtime)    │
└─────────────────────────────────┘
```

### Key Principles

1. **Pure Business Logic**: No infrastructure dependencies
2. **Declarative Rules**: Express what's valid, not how to validate
3. **Type Safety**: Strong typing for node types and data
4. **Composability**: Rules can be combined and extended
5. **Domain Language**: Uses business terminology

## Core Components

### 1. Connection Rules (`connection_rules.py`)

Defines which node types can connect to each other:

```python
class NodeConnectionRules:
    """Business rules for valid node connections"""
    
    @staticmethod
    def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
        """Determine if connection is allowed"""
        # Start nodes cannot have inputs
        if target_type == NodeType.START:
            return False
        
        # Endpoint nodes cannot have outputs
        if source_type == NodeType.ENDPOINT:
            return False
        
        # Output-capable nodes
        output_capable = {
            NodeType.PERSON_JOB,
            NodeType.CONDITION,
            NodeType.CODE_JOB,
            NodeType.API_JOB,
            NodeType.START
        }
        
        if source_type in output_capable:
            return target_type != NodeType.START
        
        return True
```

**Connection Constraints:**

```python
@staticmethod
def get_connection_constraints(node_type: NodeType) -> dict[str, list[NodeType]]:
    """Get input/output constraints for a node type"""
    
    if node_type == NodeType.START:
        return {
            'can_receive_from': [],  # No inputs
            'can_send_to': [all except START]
        }
    
    if node_type == NodeType.ENDPOINT:
        return {
            'can_receive_from': [all except ENDPOINT],
            'can_send_to': []  # No outputs
        }
    
    # Regular nodes
    return {
        'can_receive_from': [all except ENDPOINT],
        'can_send_to': [all except START]
    }
```

### 2. Transformation Rules (`transform_rules.py`)

Defines how data transforms between different node types:

```python
class TransformationRules:
    """Rules for data transformation between nodes"""
    
    @dataclass
    class TransformRule:
        """Single transformation rule"""
        source_type: NodeType
        target_type: NodeType
        source_field: str | None = None
        target_field: str | None = None
        transform_fn: Callable[[Any], Any] | None = None
    
    # Rule definitions
    RULES = [
        # PersonJob -> Condition: Extract boolean from response
        TransformRule(
            source_type=NodeType.PERSON_JOB,
            target_type=NodeType.CONDITION,
            source_field="response",
            target_field="condition_value",
            transform_fn=lambda x: bool(x.get("decision"))
        ),
        
        # CodeJob -> PersonJob: Format output as context
        TransformRule(
            source_type=NodeType.CODE_JOB,
            target_type=NodeType.PERSON_JOB,
            source_field="output",
            target_field="context",
            transform_fn=lambda x: {"code_result": str(x)}
        ),
        
        # ApiJob -> TemplateJob: Pass response data
        TransformRule(
            source_type=NodeType.API_JOB,
            target_type=NodeType.TEMPLATE_JOB,
            source_field="response",
            target_field="template_data",
            transform_fn=lambda x: x  # Direct pass-through
        )
    ]
    
    @classmethod
    def get_transform(cls, 
                     source: NodeType, 
                     target: NodeType) -> TransformRule | None:
        """Get transformation rule for node pair"""
        for rule in cls.RULES:
            if rule.source_type == source and rule.target_type == target:
                return rule
        return None
```

**Transformation Types:**

```python
class TransformationType(Enum):
    """Types of data transformations"""
    
    DIRECT = "direct"              # Pass through unchanged
    EXTRACT = "extract"            # Extract specific field
    FORMAT = "format"              # Reformat structure
    AGGREGATE = "aggregate"        # Combine multiple inputs
    FILTER = "filter"              # Filter data
    MAP = "map"                    # Map values
    CUSTOM = "custom"              # Custom function
```

### 3. Dynamic Order Calculator (`dynamic_order_calculator.py`)

Calculates execution order at runtime with advanced dependency resolution:

```python
class DomainDynamicOrderCalculator:
    """Calculates node execution order with condition branch validation"""
    
    def get_ready_nodes(self,
                       diagram: ExecutableDiagram,
                       node_states: dict[NodeID, NodeState],
                       context: ExecutionContext) -> list[ExecutableNode]:
        """Get nodes ready for execution"""
        ready_nodes = []
        
        for node in diagram.nodes:
            if self._is_node_ready(node, diagram, node_states, context):
                ready_nodes.append(node)
        
        # Prioritize and batch for optimal execution
        prioritized = self._prioritize_nodes(ready_nodes, context)
        batches = self._group_by_constraints(prioritized, context)
        
        return batches[0] if batches else []
    
    def _is_dependency_satisfied(self,
                                edge: Any,
                                node_states: dict[NodeID, NodeState],
                                context: ExecutionContext) -> bool:
        """Check dependency with condition branch validation"""
        source_state = node_states.get(edge.source_node_id)
        if not source_state or source_state.status not in [Status.COMPLETED, Status.MAXITER_REACHED]:
            return False
        
        # Critical: Validate condition branches
        if edge.source_output in ["condtrue", "condfalse"]:
            output = context.state.get_node_output(edge.source_node_id)
            if isinstance(output, ConditionOutput):
                active_branch, _ = output.get_branch_output()
                return edge.source_output == active_branch  # Only satisfied if on active branch
            return False
        
        return True
```

**Dependency Analysis:**

```python
def get_dependencies(self, node_id: NodeID) -> set[NodeID]:
    """Get all upstream dependencies for a node"""
    dependencies = set()
    
    for edge in self.diagram.edges:
        if edge.target_node_id == node_id:
            dependencies.add(edge.source_node_id)
            
            # Recursive dependencies for complex flows
            if self._is_complex_node(edge.source_node_id):
                dependencies.update(
                    self.get_dependencies(edge.source_node_id)
                )
    
    return dependencies
```

**Parallel Execution Detection:**

```python
def get_parallel_groups(self) -> list[set[NodeID]]:
    """Identify groups of nodes that can execute in parallel"""
    groups = []
    remaining = set(self.diagram.node_ids)
    
    while remaining:
        # Find nodes with no dependencies on remaining nodes
        parallel_group = set()
        
        for node_id in remaining:
            deps = self.get_dependencies(node_id)
            if not deps.intersection(remaining):
                parallel_group.add(node_id)
        
        if parallel_group:
            groups.append(parallel_group)
            remaining -= parallel_group
        else:
            # Circular dependency detected
            raise CyclicDependencyError(remaining)
    
    return groups
```

### 4. Runtime Input Resolution (`resolution/`)

Handles runtime resolution of node inputs during execution:

**Components:**
- `api.py` - Main entry point `resolve_inputs()` for resolving all inputs
- `transformation_engine.py` - `TransformationEngine` for applying data transformations
- `node_strategies.py` - Node-type-specific resolution strategies (PersonJob, Condition, etc.)
- `data_structures.py` - Value objects like `InputResolutionContext`, `ValidationResult`
- `selectors.py` - Edge selection logic for determining which inputs are ready
- `defaults.py` - Default value application for missing inputs
- `errors.py` - Resolution-specific exceptions

**Key Features:**
- Resolves actual values from executed nodes
- Applies transformation rules at runtime
- Handles special inputs (iteration counts, diagram info)
- Supports spread/pack modes for data flow
- Node-specific strategies for custom behavior

```python
from dipeo.domain.execution.resolution import resolve_inputs

# Called by handlers during execution
inputs = resolve_inputs(node, diagram, execution_context)
```

## Business Rules

### Node Type Rules

```python
class NodeTypeRules:
    """Business rules for specific node types"""
    
    # Start Node Rules
    START_RULES = {
        "max_count": 1,              # Only one start node allowed
        "required": True,             # Must have a start node
        "allows_input": False,        # Cannot receive inputs
        "requires_output": True       # Must have at least one output
    }
    
    # Endpoint Node Rules
    ENDPOINT_RULES = {
        "max_count": None,            # Multiple endpoints allowed
        "required": False,            # Optional
        "allows_output": False,       # Cannot send outputs
        "requires_input": True        # Must have at least one input
    }
    
    # Condition Node Rules
    CONDITION_RULES = {
        "max_outputs": 2,             # True/False branches
        "requires_boolean": True,     # Must evaluate to boolean
        "branch_labels": ["true", "false"]
    }
    
    # PersonJob Node Rules
    PERSON_JOB_RULES = {
        "requires_person": True,      # Must specify a person
        "allows_memory": True,        # Can access conversation memory
        "max_retries": 3              # Retry on failure
    }
```

### Data Flow Rules

```python
class DataFlowRules:
    """Rules for data flow between nodes"""
    
    @staticmethod
    def validate_data_compatibility(source_output: type, target_input: type) -> bool:
        """Check if data types are compatible"""
        # Direct compatibility
        if source_output == target_input:
            return True
        
        # Subclass compatibility
        if issubclass(source_output, target_input):
            return True
        
        # Transformation available
        if TransformationRules.has_transform(source_output, target_input):
            return True
        
        return False
    
    @staticmethod
    def get_required_fields(node_type: NodeType) -> list[str]:
        """Get required input fields for node type"""
        REQUIRED_FIELDS = {
            NodeType.PERSON_JOB: ["prompt"],
            NodeType.CODE_JOB: ["code", "language"],
            NodeType.API_JOB: ["endpoint", "method"],
            NodeType.TEMPLATE_JOB: ["template", "data"],
            NodeType.CONDITION: ["expression"]
        }
        return REQUIRED_FIELDS.get(node_type, [])
```

### Execution Flow Rules

```python
class ExecutionFlowRules:
    """Rules governing execution flow"""
    
    @staticmethod
    def should_skip_node(node: ExecutableNode, context: ExecutionContext) -> bool:
        """Determine if node should be skipped"""
        # Skip if conditional branch not taken
        if node.is_conditional_target:
            condition_result = context.get_condition_result(node.condition_id)
            if not condition_result.matches_branch(node.branch):
                return True
        
        # Skip if max iterations reached
        if node.max_iterations:
            current = context.get_iteration_count(node.id)
            if current >= node.max_iterations:
                return True
        
        # Skip if dependencies failed (unless error handling)
        dependencies = context.get_dependencies(node.id)
        if any(context.is_failed(dep) for dep in dependencies):
            if not node.handles_errors:
                return True
        
        return False
```

## Usage Examples

### Validate Connection

```python
# Check if connection is valid
source_type = NodeType.PERSON_JOB
target_type = NodeType.CONDITION

if NodeConnectionRules.can_connect(source_type, target_type):
    print("Connection allowed")
else:
    print("Invalid connection")

# Get all valid targets for a node type
constraints = NodeConnectionRules.get_connection_constraints(NodeType.START)
valid_targets = constraints['can_send_to']
```

### Apply Transformation

```python
# Get transformation rule
rule = TransformationRules.get_transform(
    NodeType.CODE_JOB,
    NodeType.PERSON_JOB
)

if rule:
    # Apply transformation
    source_data = {"output": "code execution result"}
    target_data = rule.transform_fn(source_data["output"])
    print(f"Transformed: {target_data}")
```

### Calculate Execution Order

```python
# Initialize calculator
calculator = DynamicOrderCalculator(executable_diagram)

# Track execution state
completed = {"start-node"}
failed = set()
running = {"person-job-1"}

# Get next nodes to execute
ready_nodes = calculator.get_ready_nodes(completed, failed, running)
print(f"Ready to execute: {ready_nodes}")

# Get parallel execution groups
parallel_groups = calculator.get_parallel_groups()
for i, group in enumerate(parallel_groups):
    print(f"Parallel group {i}: {group}")
```

### Validate Data Flow

```python
# Check data compatibility
source_output_type = dict
target_input_type = str

if DataFlowRules.validate_data_compatibility(source_output_type, target_input_type):
    print("Data types compatible (with transformation)")
else:
    print("Incompatible data types")

# Get required fields
required = DataFlowRules.get_required_fields(NodeType.API_JOB)
print(f"Required fields for API_JOB: {required}")
```

## Advanced Features

### Custom Rules

```python
class CustomExecutionRules(ExecutionFlowRules):
    """Extended execution rules"""
    
    @staticmethod
    def should_retry_node(node: ExecutableNode, error: Exception) -> bool:
        """Custom retry logic"""
        if isinstance(error, TemporaryError):
            return node.retry_count < node.max_retries
        return False
    
    @staticmethod
    def get_retry_delay(retry_count: int) -> float:
        """Exponential backoff for retries"""
        return min(2 ** retry_count, 60)  # Max 60 seconds
```

### Rule Composition

```python
class CompositeRule:
    """Combine multiple rules"""
    
    def __init__(self, rules: list[Callable]):
        self.rules = rules
    
    def evaluate(self, *args, **kwargs) -> bool:
        """All rules must pass"""
        return all(rule(*args, **kwargs) for rule in self.rules)

# Compose connection and data flow rules
composite = CompositeRule([
    lambda s, t: NodeConnectionRules.can_connect(s, t),
    lambda s, t: DataFlowRules.validate_data_compatibility(s, t)
])
```

### Dynamic Rule Loading

```python
class RuleRegistry:
    """Registry for dynamic rule loading"""
    
    _rules: dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, rule: Any):
        """Register a rule"""
        cls._rules[name] = rule
    
    @classmethod
    def get(cls, name: str) -> Any:
        """Get registered rule"""
        return cls._rules.get(name)

# Register custom rules
RuleRegistry.register("custom_connection", CustomConnectionRule())
RuleRegistry.register("custom_transform", CustomTransformRule())
```

## Testing

### Unit Tests

```python
def test_connection_rules():
    """Test connection validation"""
    # Valid connections
    assert NodeConnectionRules.can_connect(NodeType.START, NodeType.PERSON_JOB)
    assert NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.ENDPOINT)
    
    # Invalid connections
    assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.PERSON_JOB)
    assert not NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.START)

def test_transformation_rules():
    """Test data transformation"""
    rule = TransformationRules.get_transform(
        NodeType.PERSON_JOB,
        NodeType.CONDITION
    )
    
    assert rule is not None
    result = rule.transform_fn({"decision": True})
    assert result is True
```

### Integration Tests

```python
def test_execution_flow():
    """Test complete execution flow rules"""
    diagram = create_test_diagram()
    calculator = DynamicOrderCalculator(diagram)
    
    # Simulate execution
    completed = set()
    for node_id in ["start", "job1", "condition"]:
        ready = calculator.get_ready_nodes(completed, set(), set())
        assert node_id in ready
        completed.add(node_id)
```

## Performance Considerations

- **Rule Caching**: Cache rule evaluations for repeated checks
- **Dependency Graph**: Build once and reuse during execution
- **Parallel Detection**: Pre-compute parallel groups
- **Lazy Evaluation**: Evaluate rules only when needed
- **Index Optimization**: Use indices for fast lookups

## Dependencies

**Internal:**
- `dipeo.diagram_generated` - Generated node types
- `dipeo.domain.diagram.models` - Diagram models
- `dipeo.domain.diagram.compilation` - Compile-time resolution interfaces
- `dipeo.domain.events` - Event contracts (consolidated from messaging)

**External:**
- Python 3.13+ standard library
- `dataclasses` - Data structures
- `enum` - Enumerations
- `typing` - Type hints

## Future Enhancements

- **Rule Versioning**: Support different rule versions
- **Rule Composition Language**: DSL for complex rules
- **Machine Learning Rules**: Learn rules from execution history
- **Rule Optimization**: Optimize rule evaluation order
- **Visual Rule Builder**: UI for creating custom rules
