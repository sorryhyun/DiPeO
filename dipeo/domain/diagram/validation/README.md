# Diagram Validation Architecture

## Overview

The validation module provides a **clear separation** between structural and business validation:

- **Structural Validation**: Schema, types, connections, graph integrity → Handled by **compiler phases**
- **Business Validation**: Person references, API keys, domain rules → Handled by **business validators**

The compiler is the **single source of truth** for structural validation, ensuring validation logic stays synchronized with compilation logic.

## Architecture

### Module Structure

```
validation/
├── __init__.py             # Lazy imports to break circular dependency
├── service.py              # Thin wrapper functions using compiler
├── diagram_validator.py    # Façade implementing BaseValidator interface
├── business_validators.py  # Business validation rules (person refs, API keys)
└── utils.py                # Shared validation utilities (used by compiler)
```

### Validation Flow

```
User Code / Application Layer
   ↓
ValidateDiagramUseCase
   ↓
DiagramValidator (BaseValidator façade)
   ↓
   ├─> Structural Validation: validate_diagram() → Compiler phases
   │                                                  ↓
   │                                        [Uses validation/utils.py]
   │
   └─> Business Validation: BusinessValidatorRegistry
                                ↓
                      PersonReferenceValidator
                      APIKeyValidator (optional)
```

### Two-Layer Validation System

#### Layer 1: Structural Validation (Compiler)
- **Where**: Compilation phases (`compilation/phases/validation_phase.py`)
- **What**: Schema validation, node types, connections, graph structure
- **How**: Runs through compiler with `validate_diagram()` or phase-specific functions
- **Used by**: Both validation and compilation

#### Layer 2: Business Validation (Domain Rules)
- **Where**: Business validators (`validation/business_validators.py`)
- **What**: Person references, API key validity, domain-specific business rules
- **How**: Separate validator classes in a registry pattern
- **Used by**: Validation only (not needed for compilation)

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

### Option 1: Structural Validation (Compiler Phases)

For validation that checks diagram structure, types, or connections:

**Step 1**: Add utilities to `validation/utils.py`:

```python
def validate_my_structural_check(node: DomainNode) -> list[str]:
    """Validate structural aspect of a node."""
    errors = []
    # ... validation logic
    return errors
```

**Step 2**: Use in appropriate compiler phase (e.g., `ValidationPhase`, `ConnectionResolutionPhase`):

```python
from dipeo.domain.diagram.validation.utils import validate_my_structural_check

# In phase execute() method:
errors = validate_my_structural_check(node)
for error in errors:
    context.result.add_error(self.phase_type, error, node_id=node.id)
```

### Option 2: Business Validation (Domain Rules)

For validation that checks business rules, external references, or domain constraints:

**Step 1**: Create validator class in `validation/business_validators.py`:

```python
class MyBusinessValidator:
    """Validates my business rule."""

    def __init__(self, external_service=None):
        self.external_service = external_service

    def validate(self, diagram: DomainDiagram) -> list[ValidationError]:
        """Validate business rule."""
        errors = []
        # ... business validation logic
        return errors
```

**Step 2**: Register in `BusinessValidatorRegistry`:

```python
class BusinessValidatorRegistry:
    def __init__(self, api_key_service=None, my_service=None):
        self.validators = [
            PersonReferenceValidator(),
            # Add new validator
            MyBusinessValidator(my_service) if my_service else None,
        ]
        # Filter out None validators
        self.validators = [v for v in self.validators if v]
```

### Decision Guide: Structural vs Business?

**Use Structural Validation (compiler) if**:
- Checks diagram schema, types, or structure
- Required for compilation to succeed
- Independent of external services
- Examples: node type validation, connection validation, graph integrity

**Use Business Validation (business validators) if**:
- Checks domain-specific business rules
- Validates references to external entities
- Requires external services (API keys, databases)
- Examples: person reference validation, API key validation, quota checks

## API Reference

### High-Level API (Application Layer)

```python
# Recommended: Use through ValidateDiagramUseCase
from dipeo.application.diagram.use_cases import ValidateDiagramUseCase

use_case = ValidateDiagramUseCase()
result = use_case.validate(diagram)  # ValidationResult

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
```

### Direct Validation API (Domain Layer)

```python
# DiagramValidator (combines structural + business validation)
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator

validator = DiagramValidator(api_key_service=None)
result = validator.validate(diagram)  # ValidationResult

# Convenience functions
from dipeo.domain.diagram.validation.diagram_validator import validate_or_raise, is_valid

validate_or_raise(diagram, api_key_service=None)  # Raises ValidationError
is_valid(diagram, api_key_service=None)  # Returns bool

# Low-level structural validation functions (returns CompilationResult)
from dipeo.domain.diagram.validation import (
    validate_diagram,              # Full compilation
    validate_structure_only,       # Structure only
    validate_connections,          # Structure + connections
    collect_diagnostics,           # Custom phase
)

result = validate_diagram(diagram)
for error in result.errors:
    print(f"Error: {error.message}")
```

### Business Validators (Domain Layer)

```python
from dipeo.domain.diagram.validation.business_validators import (
    PersonReferenceValidator,
    APIKeyValidator,
    BusinessValidatorRegistry,
)

# Individual validators
person_validator = PersonReferenceValidator()
errors = person_validator.validate(diagram)

# Or use registry (recommended)
registry = BusinessValidatorRegistry(api_key_service=my_service)
errors = registry.validate(diagram)
```

### Structural Validation Utilities (Used by Compiler)

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

1. **Use the compiler as the source of truth**: All structural validation should use compiler phases
2. **Separate structural from business validation**:
   - Structural → compiler phases + `validation/utils.py`
   - Business → business validators in `validation/business_validators.py`
3. **Keep utils.py pure**: No imports from compilation modules (to avoid circular dependencies)
4. **Document validation rules**: Add clear docstrings explaining what each check does
5. **Return structured errors**: Use `CompilationError` for structural, `ValidationError` for business
6. **Don't circumvent lazy imports**: Always import from `validation/`, not directly from `service.py`
7. **Use the registry pattern**: Register new business validators in `BusinessValidatorRegistry`
8. **Prefer use cases**: Application code should use `ValidateDiagramUseCase`, not validators directly

## Common Patterns

### Application Layer: Using ValidateDiagramUseCase

```python
from dipeo.application.diagram.use_cases import ValidateDiagramUseCase

use_case = ValidateDiagramUseCase()
result = use_case.validate(diagram)

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
```

### Domain Layer: Using DiagramValidator Directly

```python
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator

# With API key validation
validator = DiagramValidator(api_key_service=my_service)
result = validator.validate(diagram)

# Or use convenience function
from dipeo.domain.diagram.validation.diagram_validator import validate_or_raise

try:
    validate_or_raise(diagram, api_key_service=my_service)
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Compiler Layer: Using Validation Utilities

```python
from dipeo.domain.diagram.validation.utils import validate_arrow_handles

# In a compilation phase
errors = validate_arrow_handles(arrow, node_ids)
for error in errors:
    context.result.add_error(self.phase_type, error, arrow_id=arrow.id)
```

### Adding Custom Business Validator

```python
# 1. Create validator
from dipeo.domain.diagram.validation.business_validators import BusinessValidatorRegistry
from dipeo.domain.base.exceptions import ValidationError

class QuotaValidator:
    def __init__(self, quota_service):
        self.quota_service = quota_service

    def validate(self, diagram):
        errors = []
        if len(diagram.nodes) > self.quota_service.max_nodes:
            errors.append(ValidationError("Too many nodes"))
        return errors

# 2. Add to registry (modify BusinessValidatorRegistry.__init__)
# self.validators.append(QuotaValidator(quota_service))
```
