# Diagram Validation Architecture

## Overview

The validation module provides diagram validation through the domain compiler as the single source of truth. This ensures validation logic stays synchronized with compilation logic.

## Architecture

### Module Structure

```
validation/
├── __init__.py          # Lazy imports to break circular dependency
├── service.py           # Main validation functions using compiler
├── diagram_validator.py # Façade implementing BaseValidator interface
└── utils.py             # Shared validation utilities
```

### Validation Flow

```
User Code
   ↓
diagram_validator.DiagramValidator (BaseValidator façade)
   ↓
validation.validate_diagram() [lazy import via __init__.py]
   ↓
service.validate_diagram()
   ↓
DomainDiagramCompiler.compile_with_diagnostics()
   ↓
[Compiler uses validation/utils.py for checks]
```

## Circular Dependency Resolution

**Problem**: `validation` needs `DomainDiagramCompiler`, but `compilation` modules use `validation/utils.py`

**Solution**: Lazy imports in `validation/__init__.py`

```python
def __getattr__(name):
    if name in ["validate_diagram", ...]:
        from .service import validate_diagram
        return validate_diagram
```

This defers the import of `service.py` (which imports the compiler) until the function is actually called, breaking the circular dependency at module load time.

## Validation Levels

### 1. Structure Only (`validate_structure_only`)
- Stops after: `CompilationPhase.VALIDATION`
- Checks: Missing nodes, duplicate IDs, invalid types, basic integrity
- Use when: You only need basic structural validation

### 2. Connection Validation (`validate_connections`)
- Stops after: `CompilationPhase.CONNECTION_RESOLUTION`
- Checks: Structure + transformations + handles + connection validity
- Use when: You need to validate data flow

### 3. Full Validation (`validate_diagram`)
- Runs: Complete compilation with diagnostics
- Checks: Everything including node factory and executable diagram
- Use when: You need comprehensive validation

### 4. Diagnostics Collection (`collect_diagnostics`)
- Flexible: Specify custom stop phase
- Use when: You need fine-grained control

## Adding New Validation Logic

### Option 1: Add to Shared Utils (Preferred for reusable checks)

Add to `validation/utils.py`:

```python
def validate_my_check(node: DomainNode) -> list[str]:
    """Validate something about a node."""
    errors = []
    # ... validation logic
    return errors
```

Use from compiler or other modules:

```python
from dipeo.domain.diagram.validation.utils import validate_my_check
```

### Option 2: Add to Compiler Phase

For phase-specific validation, add logic directly in the appropriate compiler phase (e.g., `ConnectionResolver`, `EdgeBuilder`, etc.)

### Option 3: Add to DiagramValidator

For application-level validation (e.g., checking API keys), add to `diagram_validator.py:_validate_diagram()`

## API Reference

### Public Functions

```python
# High-level façade (implements BaseValidator)
validator = DiagramValidator(api_key_service=None)
result = validator.validate(diagram)

# Or convenience functions
validate_or_raise(diagram, api_key_service=None)
is_valid(diagram, api_key_service=None) -> bool

# Direct validation functions
validate_diagram(diagram) -> CompilationResult
validate_structure_only(diagram) -> CompilationResult
validate_connections(diagram) -> CompilationResult
collect_diagnostics(diagram, stop_after=None) -> CompilationResult
```

### Shared Utilities

```python
from dipeo.domain.diagram.validation.utils import (
    validate_arrow_handles,
    validate_node_type_connections,
    validate_condition_node_branches,
    find_node_dependencies,
    find_unreachable_nodes,
)
```

## Best Practices

1. **Use the compiler as the source of truth**: Don't duplicate validation logic
2. **Keep utils.py pure**: No imports from compilation modules
3. **Document validation rules**: Add docstrings explaining what each check does
4. **Return structured errors**: Use `CompilationError` for consistency
5. **Don't circumvent lazy imports**: Always import validation functions from `validation/`, not directly from `service.py`

## Common Patterns

### From Application Code

```python
from dipeo.domain.diagram.validation import validate_diagram

result = validate_diagram(diagram)
if result.errors:
    for error in result.errors:
        print(f"Error: {error.message}")
```

### From Compilation Code

```python
from dipeo.domain.diagram.validation.utils import validate_arrow_handles

errors = validate_arrow_handles(arrow, node_ids)
if errors:
    compilation_result.add_errors(errors)
```

### Using the Façade

```python
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator

validator = DiagramValidator(api_key_service=my_service)
result = validator.validate(diagram)
if not result.is_valid:
    raise ValidationError(result.errors)
```
