# Business Rules

## Overview

The `rules/` module defines business rules for diagram execution:

1. **NodeConnectionRules**: Which node types can connect to each other
2. **DataTransformRules**: How data transforms between node types

These rules are **compile-time and runtime invariants** enforced by the validation and execution systems.

## NodeConnectionRules

**Location:** `dipeo/domain/execution/rules/connection_rules.py:6`

Defines valid connections between node types.

### Implementation

```python
class NodeConnectionRules:
    @staticmethod
    def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
        """Check if a connection is allowed."""

    @staticmethod
    def get_connection_constraints(node_type: NodeType) -> dict[str, list[NodeType]]:
        """Get valid source/target types for a node."""
```

### Rules

#### START Nodes

```python
# START cannot receive inputs
NodeConnectionRules.can_connect(anything, NodeType.START)  # False

# START can send to anything except START
NodeConnectionRules.can_connect(NodeType.START, NodeType.PERSON_JOB)  # True
NodeConnectionRules.can_connect(NodeType.START, NodeType.START)  # False
```

#### ENDPOINT Nodes

```python
# ENDPOINT can receive inputs
NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.ENDPOINT)  # True

# ENDPOINT cannot send outputs
NodeConnectionRules.can_connect(NodeType.ENDPOINT, anything)  # False
```

#### Output-Capable Nodes

```python
output_capable = {
    NodeType.PERSON_JOB,
    NodeType.CONDITION,
    NodeType.CODE_JOB,
    NodeType.API_JOB,
    NodeType.START
}

# These can send to anything except START
for node_type in output_capable:
    assert NodeConnectionRules.can_connect(node_type, NodeType.PERSON_JOB)
    assert not NodeConnectionRules.can_connect(node_type, NodeType.START)
```

#### General Rule

```python
# Most nodes can connect to anything except START
NodeConnectionRules.can_connect(source, target)
# True unless:
#   - target is START
#   - source is ENDPOINT
```

### Usage

#### Validation (Compile Time)

```python
# In diagram validation
for edge in diagram.edges:
    source_node = diagram.get_node(edge.source_node_id)
    target_node = diagram.get_node(edge.target_node_id)

    if not NodeConnectionRules.can_connect(source_node.type, target_node.type):
        raise ValidationError(
            f"Invalid connection: {source_node.type} -> {target_node.type}"
        )
```

#### UI (Diagram Editor)

```python
# When user drags an edge
if not NodeConnectionRules.can_connect(source_type, target_type):
    show_error("Cannot connect these node types")
    prevent_drop()
```

#### Query Constraints

```python
# Get valid targets for a node
constraints = NodeConnectionRules.get_connection_constraints(NodeType.START)

# constraints = {
#     "can_receive_from": [],  # START has no inputs
#     "can_send_to": [NodeType.PERSON_JOB, NodeType.CODE_JOB, ...]  # All except START
# }

# Use in UI to show valid drop targets
valid_targets = constraints["can_send_to"]
```

### Implementation Details

```python
# dipeo/domain/execution/rules/connection_rules.py

@staticmethod
def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
    # Rule 1: START cannot receive
    if target_type == NodeType.START:
        return False

    # Rule 2: ENDPOINT cannot send
    if source_type == NodeType.ENDPOINT:
        return False

    # Rule 3: Output-capable nodes
    output_capable = {
        NodeType.PERSON_JOB,
        NodeType.CONDITION,
        NodeType.CODE_JOB,
        NodeType.API_JOB,
        NodeType.START,
    }

    if source_type in output_capable:
        return target_type != NodeType.START

    # Default: allow
    return True
```

**Lines:** 48 total (simple implementation)

### Future Extensions

Planned enhancements (not yet implemented):

```python
# 1. Port-specific rules
def can_connect_ports(
    source_type: NodeType, source_port: str,
    target_type: NodeType, target_port: str
) -> bool:
    """Check if specific ports can connect."""
    # E.g., Condition.condtrue can only connect to execution inputs

# 2. Cardinality rules
def get_max_inputs(node_type: NodeType) -> int | None:
    """Get max allowed inputs."""
    # E.g., Condition has max 2 outputs (condtrue, condfalse)

# 3. Required connections
def get_required_outputs(node_type: NodeType) -> list[str]:
    """Get required output ports."""
    # E.g., START must have at least one output
```

## DataTransformRules

**Location:** `dipeo/domain/execution/rules/transform_rules.py:11`

Defines type-based data transformations between nodes.

### Implementation

```python
class DataTransformRules:
    @staticmethod
    def get_data_transform(source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Get transformation rules based on node types."""

    @staticmethod
    def merge_transforms(
        edge_transform: dict[str, Any],
        type_based_transform: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge edge-specific and type-based transformations."""
```

**Lines:** 26 total (minimal implementation)

### Current Rules

#### PersonJob with Tools

```python
# If PersonJob has tools, extract tool results
source = PersonJobNode(tools=["calculator", "web_search"], ...)
transforms = DataTransformRules.get_data_transform(source, target)

# transforms = {"extract_tool_results": True}
```

Used during input resolution to extract tool outputs from PersonJob response.

#### No Other Rules

Currently, this is the **only** transformation rule. More will be added as needed.

### Usage

#### During Input Resolution

```python
# In resolution/api.py:transform_edge_values()

source_node = diagram.get_node(edge.source_node_id)
target_node = diagram.get_node(edge.target_node_id)

# Get type-based rules
type_rules = DataTransformRules.get_data_transform(source_node, target_node)

# Get edge-specific rules
edge_rules = getattr(edge, "transform_rules", {}) or {}

# Merge (edge rules take precedence)
rules = DataTransformRules.merge_transforms(edge_rules, type_rules)

# Apply transformations
transformed_value = transformation_engine.transform(value, rules)
```

#### Merge Semantics

```python
edge_rules = {"custom_rule": "value"}
type_rules = {"extract_tool_results": True}

merged = DataTransformRules.merge_transforms(edge_rules, type_rules)
# merged = {"extract_tool_results": True, "custom_rule": "value"}

# Edge rules override type rules
edge_rules = {"extract_tool_results": False}  # Override
type_rules = {"extract_tool_results": True}

merged = DataTransformRules.merge_transforms(edge_rules, type_rules)
# merged = {"extract_tool_results": False}  # Edge rule wins
```

### Implementation Details

```python
# dipeo/domain/execution/rules/transform_rules.py

@staticmethod
def get_data_transform(source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
    transforms = {}

    # Rule: PersonJob with tools -> extract tool results
    if isinstance(source, PersonJobNode) and source.tools:
        transforms["extract_tool_results"] = True

    return transforms

@staticmethod
def merge_transforms(
    edge_transform: dict[str, Any],
    type_based_transform: dict[str, Any]
) -> dict[str, Any]:
    # Type rules first, then edge rules (edge rules override)
    return {**type_based_transform, **edge_transform}
```

### Future Extensions

**Planned (not yet implemented):**

```python
# 1. Typed transformations with dataclass
@dataclass
class TransformRule:
    source_type: NodeType
    target_type: NodeType
    source_field: str | None
    target_field: str | None
    transform_fn: Callable[[Any], Any] | None

# 2. Transformation registry
RULES = [
    TransformRule(
        source_type=NodeType.PERSON_JOB,
        target_type=NodeType.CONDITION,
        source_field="response",
        target_field="condition_value",
        transform_fn=lambda x: bool(x.get("decision"))
    ),
    TransformRule(
        source_type=NodeType.CODE_JOB,
        target_type=NodeType.PERSON_JOB,
        source_field="output",
        target_field="context",
        transform_fn=lambda x: {"code_result": str(x)}
    ),
]

# 3. Transformation types enum
class TransformationType(Enum):
    DIRECT = "direct"        # Pass through
    EXTRACT = "extract"      # Extract field
    FORMAT = "format"        # Reformat
    AGGREGATE = "aggregate"  # Combine multiple
    FILTER = "filter"        # Filter data
    MAP = "map"              # Map values
    CUSTOM = "custom"        # Custom function

# 4. Data type compatibility checking
def validate_data_compatibility(
    source_output_type: type,
    target_input_type: type
) -> bool:
    """Check if data types are compatible."""
    # Direct match
    if source_output_type == target_input_type:
        return True
    # Subclass
    if issubclass(source_output_type, target_input_type):
        return True
    # Transformation available
    if has_transform(source_output_type, target_input_type):
        return True
    return False
```

## Design Rationale

### Why Separate Connection and Transform Rules?

**Connection rules**: Structural constraints (graph topology)
**Transform rules**: Data flow constraints (values)

Separation allows:
- Independent validation (structure vs data)
- Clear responsibilities
- Different enforcement points (compile-time vs runtime)

### Why Minimal Implementation?

Current implementation is intentionally minimal:
- **YAGNI**: Only implement rules as needed
- **Simplicity**: Easy to understand and maintain
- **Extensibility**: Clear path to add more rules

As the system grows, more rules will be added following the established pattern.

### Why Static Methods?

Rules are **pure functions** with no state:
- No need for instance state
- Clear that they're stateless
- Easy to test (no setup required)
- Can be called directly without instantiation

## Testing

```python
def test_connection_rules():
    """Test connection validation."""
    # Valid connections
    assert NodeConnectionRules.can_connect(
        NodeType.START,
        NodeType.PERSON_JOB
    )
    assert NodeConnectionRules.can_connect(
        NodeType.PERSON_JOB,
        NodeType.ENDPOINT
    )
    assert NodeConnectionRules.can_connect(
        NodeType.CODE_JOB,
        NodeType.CONDITION
    )

    # Invalid connections
    assert not NodeConnectionRules.can_connect(
        NodeType.PERSON_JOB,
        NodeType.START
    )
    assert not NodeConnectionRules.can_connect(
        NodeType.ENDPOINT,
        NodeType.PERSON_JOB
    )

def test_connection_constraints():
    """Test constraint queries."""
    # START
    constraints = NodeConnectionRules.get_connection_constraints(NodeType.START)
    assert constraints["can_receive_from"] == []
    assert NodeType.START not in constraints["can_send_to"]

    # ENDPOINT
    constraints = NodeConnectionRules.get_connection_constraints(NodeType.ENDPOINT)
    assert constraints["can_send_to"] == []
    assert NodeType.ENDPOINT not in constraints["can_receive_from"]

def test_transform_rules():
    """Test data transformation rules."""
    # PersonJob with tools
    source = PersonJobNode(tools=["calculator"], ...)
    target = ConditionNode(...)

    transforms = DataTransformRules.get_data_transform(source, target)
    assert transforms["extract_tool_results"] is True

    # PersonJob without tools
    source = PersonJobNode(tools=None, ...)
    transforms = DataTransformRules.get_data_transform(source, target)
    assert "extract_tool_results" not in transforms

def test_transform_merge():
    """Test rule merging."""
    edge_rules = {"custom": "value"}
    type_rules = {"extract_tool_results": True}

    merged = DataTransformRules.merge_transforms(edge_rules, type_rules)

    assert merged["custom"] == "value"
    assert merged["extract_tool_results"] is True

    # Edge rules override
    edge_rules = {"extract_tool_results": False}
    merged = DataTransformRules.merge_transforms(edge_rules, type_rules)
    assert merged["extract_tool_results"] is False
```

## Usage in Codebase

### Connection Rules

**Used by:**
- `dipeo/domain/diagram/compilation/validation/` - Compile-time validation
- UI diagram editor - Connection validation
- GraphQL API - Mutation validation

**Example:**
```python
# In validation phase
for edge in diagram.edges:
    if not NodeConnectionRules.can_connect(
        source_node.type,
        target_node.type
    ):
        errors.append(f"Invalid connection: {edge}")
```

### Transform Rules

**Used by:**
- `dipeo/domain/execution/resolution/api.py` - Input resolution
- `dipeo/domain/execution/resolution/transformation_engine.py` - Data transformation

**Example:**
```python
# In input resolution
type_rules = DataTransformRules.get_data_transform(source_node, target_node)
edge_rules = edge.transform_rules or {}
rules = DataTransformRules.merge_transforms(edge_rules, type_rules)

transformed = transformation_engine.transform(value, rules)
```

## Related Components

- **Validation** (`dipeo/domain/diagram/compilation/validation/`): Enforces connection rules
- **Resolution** (`dipeo/domain/execution/resolution/`): Applies transform rules
- **TransformationEngine** (`resolution/transformation_engine.py`): Executes transformations

## Future Enhancements

**Planned but not yet implemented:**

1. **Rule Registry** (Task 31):
   ```python
   class RuleRegistry:
       """Dynamic rule loading."""
       _rules: dict[str, Any] = {}

       @classmethod
       def register(cls, name: str, rule: Any): ...

       @classmethod
       def get(cls, name: str) -> Any: ...
   ```

2. **Advanced Transform Rules**:
   - Field-level mappings
   - Transformation functions
   - Type compatibility checking
   - Validation with Pydantic

3. **Port-Specific Rules**:
   - Different rules per port
   - Port cardinality constraints
   - Required vs optional ports

4. **Conditional Rules**:
   - Rules based on node configuration
   - Dynamic rule selection
   - Context-dependent transformations

5. **Rule Composition**:
   - Combine multiple rules
   - Rule priorities
   - Override mechanisms

6. **Rule Documentation**:
   - Auto-generated rule docs
   - Visual rule viewer in UI
   - Rule violation explanations
