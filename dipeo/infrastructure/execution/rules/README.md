# Execution Rule Registry

This module implements a pluggable, extensible registry pattern for execution rules, replacing the previous static method approach with a dynamic, type-safe system.

## Overview

The ExecutionRuleRegistry provides a centralized, thread-safe system for managing:
- **Connection Rules**: Define which node types can connect to each other
- **Transform Rules**: Define how data should be transformed between nodes

## Key Features

- **Type-safe registration** with metadata
- **Priority-based execution** for rule ordering
- **Thread-safe** operations with RLock
- **Audit trails** for all registry operations
- **Immutable rules** that cannot be overridden
- **Freezable registry** to prevent modifications in production
- **Backward compatible** with existing static rule classes
- **Extensible** - easy to add custom rules

## Quick Start

### Using Existing Rules (Backward Compatible)

The existing `NodeConnectionRules` and `DataTransformRules` classes continue to work exactly as before:

```python
from dipeo.domain.execution.rules import NodeConnectionRules, DataTransformRules
from dipeo.diagram_generated import NodeType

# Check if connection is allowed
can_connect = NodeConnectionRules.can_connect(
    NodeType.START,
    NodeType.PERSON_JOB
)  # True

# Get connection constraints
constraints = NodeConnectionRules.get_connection_constraints(NodeType.START)
# Returns: {"can_receive_from": [], "can_send_to": [...]}

# Get data transforms
transforms = DataTransformRules.get_data_transform(source_node, target_node)

# Merge transforms
merged = DataTransformRules.merge_transforms(edge_transform, type_transform)
```

### Registering Custom Rules

To add custom rules, access the underlying registry:

```python
from dipeo.domain.execution.rules import NodeConnectionRules
from dipeo.infrastructure.execution.rules import (
    BaseConnectionRule,
    RuleKey,
    RuleCategory,
    RulePriority,
)
from dipeo.diagram_generated import NodeType

class MyCustomRule(BaseConnectionRule):
    def __init__(self):
        super().__init__(
            name="my_custom_rule",
            description="Prevents CODE_JOB to CODE_JOB connections",
            priority=RulePriority.HIGH
        )

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        # Block CODE_JOB to CODE_JOB connections
        if source_type == NodeType.CODE_JOB and target_type == NodeType.CODE_JOB:
            return False
        return True

    def get_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        if source_type == NodeType.CODE_JOB and target_type == NodeType.CODE_JOB:
            return "CODE_JOB nodes cannot connect directly to other CODE_JOB nodes"
        return None

# Get the registry
registry = NodeConnectionRules.get_registry()

# Register the custom rule
rule = MyCustomRule()
key = RuleKey(
    name=rule.name,
    category=RuleCategory.CONNECTION,
    priority=rule.priority,
    description=rule.description,
)
registry.register_connection_rule(key, rule)

# Now the rule is enforced
NodeConnectionRules.can_connect(NodeType.CODE_JOB, NodeType.CODE_JOB)  # False
```

### Custom Transform Rules

```python
from dipeo.domain.execution.rules import DataTransformRules
from dipeo.infrastructure.execution.rules import (
    BaseTransformRule,
    RuleKey,
    RuleCategory,
    RulePriority,
)

class MyTransformRule(BaseTransformRule):
    def __init__(self):
        super().__init__(
            name="my_transform",
            description="Adds custom metadata to transforms",
            priority=RulePriority.NORMAL
        )

    def applies_to(self, source, target):
        # Check if this rule should apply
        return source.type == NodeType.CODE_JOB

    def get_transform(self, source, target):
        return {
            "custom_metadata": True,
            "source_id": source.id,
        }

# Register it
registry = DataTransformRules.get_registry()
rule = MyTransformRule()
key = RuleKey(
    name=rule.name,
    category=RuleCategory.TRANSFORM,
    priority=rule.priority,
    description=rule.description,
)
registry.register_transform_rule(key, rule)
```

## Architecture

### Components

1. **Base Interfaces** (`base.py`)
   - `ConnectionRule`: Protocol for connection validation rules
   - `TransformRule`: Protocol for data transformation rules
   - `BaseConnectionRule`: Abstract base class for connection rules
   - `BaseTransformRule`: Abstract base class for transform rules

2. **Registry** (`registry.py`)
   - `ExecutionRuleRegistry`: Main registry class
   - `RuleKey`: Type-safe key with metadata
   - `RuleCategory`: Enum for rule types (CONNECTION, TRANSFORM, etc.)
   - `RulePriority`: Enum for priority levels (CRITICAL, HIGH, NORMAL, LOW, FALLBACK)

3. **Adapters** (`adapters.py`)
   - Concrete implementations of existing rules
   - `StartNoInputRule`: START nodes cannot receive input
   - `EndpointNoOutputRule`: ENDPOINT nodes cannot send output
   - `OutputCapableRule`: Output-capable nodes can only connect to non-START
   - `PersonJobToolExtractionRule`: Extract tool results from PersonJob

4. **Compatibility Layer** (`compat.py`)
   - Singleton registry instance
   - Backward-compatible wrapper classes
   - `NodeConnectionRulesCompat`: Maintains old API
   - `DataTransformRulesCompat`: Maintains old API

### Rule Priority

Rules are executed in priority order:

```python
class RulePriority(Enum):
    CRITICAL = 1000  # Must run first, cannot be overridden
    HIGH = 750       # Important rules
    NORMAL = 500     # Standard priority (default)
    LOW = 250        # Optional rules
    FALLBACK = 100   # Last resort rules
```

For connection rules, the first rule that returns `False` blocks the connection.

For transform rules, all applicable rules are merged with higher priority rules overriding lower priority ones.

### Safety Features

#### Immutable Rules

Rules can be marked as immutable to prevent override:

```python
key = RuleKey(
    name="critical_rule",
    category=RuleCategory.CONNECTION,
    priority=RulePriority.CRITICAL,
    immutable=True,  # Cannot be overridden
)
```

#### Frozen Registry

The registry can be frozen to prevent modifications:

```python
registry = NodeConnectionRules.get_registry()
registry.freeze()

# Now all registration attempts will fail
# Useful for production environments
```

#### Audit Trail

All registry operations are logged with audit trails:

```python
trail = registry.get_audit_trail()
for record in trail:
    print(f"{record.timestamp}: {record.action} - {record.rule_key}")
```

## Testing

### Running Tests

```bash
# Run all rule tests
python -m pytest tests/infrastructure/execution/rules/ -v

# Run registry tests only
python -m pytest tests/infrastructure/execution/rules/test_registry.py -v

# Run backward compatibility tests
python -m pytest tests/infrastructure/execution/rules/test_backward_compat.py -v
```

### Test Coverage

- Registry core functionality (16 tests)
- Backward compatibility (16 tests)
- Priority ordering
- Thread safety
- Immutability
- Freeze/unfreeze
- Audit trails
- Custom rule registration

## Migration Guide

### For Existing Code

No changes required! The existing code continues to work:

```python
# This still works exactly as before
from dipeo.domain.execution.rules import NodeConnectionRules

can_connect = NodeConnectionRules.can_connect(source_type, target_type)
```

### For New Features

To add custom rules, use the registry:

```python
# Access the registry
registry = NodeConnectionRules.get_registry()

# Register custom rules
registry.register_connection_rule(key, rule)
```

### For Plugins

Create a module that registers rules on import:

```python
# my_plugin/rules.py
from dipeo.domain.execution.rules import NodeConnectionRules
from dipeo.infrastructure.execution.rules import BaseConnectionRule, RuleKey, RuleCategory

class MyPluginRule(BaseConnectionRule):
    # ... implementation ...

# Auto-register when imported
def register_plugin_rules():
    registry = NodeConnectionRules.get_registry()
    rule = MyPluginRule()
    key = RuleKey(name=rule.name, category=RuleCategory.CONNECTION, priority=rule.priority)
    registry.register_connection_rule(key, rule)

register_plugin_rules()
```

## Best Practices

1. **Use descriptive names**: Rule names should clearly describe what they do
2. **Document reasons**: Implement `get_reason()` to provide clear error messages
3. **Set appropriate priorities**: Use HIGH for critical rules, NORMAL for standard
4. **Test thoroughly**: Write tests for custom rules before deployment
5. **Consider immutability**: Mark critical rules as immutable
6. **Audit in production**: Enable audit trails in production environments

## API Reference

### ExecutionRuleRegistry

Main registry class for managing execution rules.

#### Methods

- `register_connection_rule(key, rule, *, override=False, override_reason=None)`: Register a connection rule
- `register_transform_rule(key, rule, *, override=False, override_reason=None)`: Register a transform rule
- `can_connect(source_type, target_type)`: Check if connection is allowed
- `get_connection_reason(source_type, target_type)`: Get reason why connection is not allowed
- `get_connection_constraints(node_type)`: Get valid sources and targets for a node type
- `get_data_transform(source, target)`: Get transformation rules for a node pair
- `merge_transforms(edge_transform, type_based_transform)`: Merge transformations
- `unregister(key, *, force=False)`: Remove a rule
- `list_rules(category=None)`: List registered rules
- `get_rule_info(key)`: Get information about a rule
- `freeze()`: Freeze registry to prevent modifications
- `unfreeze(*, force=False)`: Unfreeze registry
- `is_frozen()`: Check if registry is frozen
- `get_audit_trail(rule_key=None)`: Get audit trail
- `temporary_override(overrides)`: Context manager for temporary rule overrides (testing only)

### RuleKey

Type-safe key for rule registration.

#### Attributes

- `name`: Unique identifier for the rule
- `category`: Rule category (CONNECTION, TRANSFORM, etc.)
- `priority`: Priority level for execution order
- `description`: Human-readable description
- `immutable`: Whether rule can be overridden
- `dependencies`: Tuple of dependency rule names

### BaseConnectionRule

Abstract base class for connection rules.

#### Methods to Implement

- `can_connect(source_type, target_type)`: Check if connection is allowed
- `get_reason(source_type, target_type)`: Get reason for rejection (optional)

### BaseTransformRule

Abstract base class for transform rules.

#### Methods to Implement

- `applies_to(source, target)`: Check if rule applies to the node pair
- `get_transform(source, target)`: Get transformation configuration

## Examples

See `tests/infrastructure/execution/rules/test_backward_compat.py` for comprehensive examples of:
- Custom connection rules
- Custom transform rules
- Priority ordering
- Registry extensibility

## Related

- [Domain Execution Module](/home/soryhyun/DiPeO/dipeo/domain/execution/rules/README.md): Original static rules documentation
- [EnhancedServiceRegistry](/home/soryhyun/DiPeO/dipeo/application/registry/enhanced_service_registry.py): Similar registry pattern for services
