# Code Generation Infrastructure

This directory contains the code generation infrastructure that transforms TypeScript specifications into Python backend code, GraphQL schemas, and frontend TypeScript models.

## Architecture Overview

### Core Components

#### IR Builders (`ir_builders/`)
The heart of the code generation system. IR (Intermediate Representation) builders parse TypeScript AST and generate structured data used by templates.

**Pipeline Architecture**:
- **`ir_builders/core/`** - Pipeline orchestration framework
  - `context.py` - Build context with caching and configuration
  - `steps.py` - Step interface and pipeline orchestrator
  - `base.py` - Base IR builder using step pipeline
  - `base_steps.py` - Reusable base step classes with template method pattern

- **`ir_builders/modules/`** - Reusable extraction and transformation steps
  - `node_specs.py` - Node specification extraction and factory building
  - `domain_models.py` - Domain model, enum, and integration extraction
  - `graphql_operations.py` - GraphQL operation extraction and grouping
  - `ui_configs.py` - UI configuration and TypeScript model generation

- **`ir_builders/builders/`** - Domain-specific builders using pipeline
  - `backend.py` - Backend code generation builder
  - `frontend.py` - Frontend models and config builder
  - `strawberry.py` - GraphQL/Strawberry schema builder

- **`ir_builders/validators/`** - IR data validators
  - `base.py` - Validation framework with result tracking
  - `backend.py` - Backend IR validation
  - `frontend.py` - Frontend IR validation
  - `strawberry.py` - GraphQL IR validation

- **`ir_builders/type_system_unified/`** - Unified type conversion system
  - `converter.py` - UnifiedTypeConverter for all type conversions
  - `resolver.py` - UnifiedTypeResolver for Strawberry field resolution
  - `registry.py` - TypeRegistry for runtime type registration
  - `type_mappings.yaml` - TypeScript → Python mappings
  - `graphql_mappings.yaml` - GraphQL → Python mappings
  - Comprehensive test suite covering all conversion paths

- **`ir_builders/ast/`** - AST processing framework
  - `walker.py` - AST traversal with visitor pattern
  - `filters.py` - File and node filtering with composition
  - `extractors.py` - Reusable extraction classes

#### Templates (`templates/`)
Jinja2 templates that consume IR data to generate code:
- **`backend/`** - Python backend code templates
- **`frontend/`** - TypeScript frontend model templates
- **`strawberry/`** - GraphQL schema templates

#### Parsers (`parsers/`)
TypeScript AST parsing utilities:
- `typescript_ast_parser.py` - Main AST parser
- `node_spec_parser.py` - Node specification extraction
- `graphql_parser.py` - GraphQL query parsing

#### Type System (`type_system/`)
Case conversion utilities (type conversion moved to `ir_builders/type_system_unified/`):
- `converter.py` - Case conversion functions (snake_case, camel_case, pascal_case, etc.)
- `__init__.py` - Exports case conversion utilities only

**Note**: TypeConverter class removed in Phase 3. Use `UnifiedTypeConverter` from `ir_builders/type_system_unified/`.

## Code Generation Workflow

### 1. Parse TypeScript → AST
```bash
make parse-typescript
```
- Reads TypeScript specs from `/dipeo/models/src/`
- Outputs AST JSON to `temp/**/*.ts.json`

### 2. Build IR → Generate Code
```bash
make codegen
```
- Loads parsed AST
- Runs IR builders (backend, frontend, strawberry)
- Applies templates with IR data
- Outputs to `dipeo/diagram_generated_staged/`

### 3. Validate & Apply
```bash
make diff-staged       # Review changes
make apply            # Apply with type checking
make apply-test       # Apply with server test
make graphql-schema   # Update GraphQL schema
```

## New Pipeline System

### How It Works

1. **BuildContext** manages shared state:
   - Configuration loading
   - Type conversion utilities
   - Step result caching
   - Metadata generation

2. **BuildStep** defines reusable operations:
   - Extract: Parse AST data
   - Transform: Convert between formats
   - Assemble: Combine into final structure
   - Validate: Check correctness

3. **PipelineOrchestrator** manages execution:
   - Dependency resolution
   - Sequential execution
   - Result propagation
   - Error handling

### Creating a New Builder

```python
from dipeo.infrastructure.codegen.ir_builders.core.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.modules import (
    ExtractNodeSpecsStep,
    BuildNodeFactoryStep,
)

class MyBuilder(BaseIRBuilder):
    def _configure_pipeline(self):
        # Add extraction steps
        self.orchestrator.add_step(ExtractNodeSpecsStep())

        # Add transformation steps
        self.orchestrator.add_step(BuildNodeFactoryStep())

        # Add custom assembly step
        self.orchestrator.add_step(MyAssemblerStep())

    def get_builder_type(self):
        return "my_builder"
```

### Creating a New Step

```python
from dipeo.infrastructure.codegen.ir_builders.core.steps import BuildStep, StepResult, StepType

class MyExtractionStep(BuildStep):
    def __init__(self):
        super().__init__(
            name="extract_my_data",
            step_type=StepType.EXTRACT,
        )
        # Define dependencies after init
        self._dependencies = ["other_step_name"]

    def execute(self, context, data):
        # Extract data from AST
        my_data = self._extract(data)

        # Access other step results via context
        other_data = context.get_step_data("other_step")

        return StepResult(
            success=True,
            data=my_data,
            metadata={"count": len(my_data)}
        )
```

## Important Files

### Configuration
- `projects/codegen/config/` - Builder-specific configuration
- Environment: `DIPEO_BASE_DIR` - Project root directory

### Generated Code Locations
- **Staged**: `dipeo/diagram_generated_staged/` - Review before applying
- **Active**: `dipeo/diagram_generated/` - Current generated code
- **GraphQL**: `apps/server/app/graphql/generated/` - GraphQL schema

### Test Data
- `projects/codegen/parsed/typescript_ast.json` - Parsed TypeScript AST
- `projects/codegen/ir/` - IR snapshots for debugging
- `projects/codegen/ir/test_outputs/` - Test comparison outputs

## Common Tasks

### Update Node Specifications
1. Edit TypeScript in `/dipeo/models/src/node-specs/`
2. Run `cd dipeo/models && pnpm build`
3. Run `make codegen`
4. Review and apply changes

### Add New GraphQL Operation
1. Define in `/dipeo/models/src/frontend/query-definitions/`
2. Build models and run codegen
3. Update GraphQL schema: `make graphql-schema`

### Debug IR Generation
1. Run test script: `python dipeo/infrastructure/codegen/ir_builders/test_new_builders.py`
2. Check outputs in `projects/codegen/ir/test_outputs/`
3. Compare old vs new builder outputs

### Validate Generated Code
```python
from dipeo.infrastructure.codegen.ir_builders.validators import get_validator

validator = get_validator("backend")
result = validator.validate(ir_data)
print(result.get_summary())
```

## Unified Type System

Configuration-driven type conversion system handling all type transformations across the codebase.

### Architecture

**Single Source of Truth**: All type conversions now go through `UnifiedTypeConverter`:
- TypeScript → Python
- TypeScript → GraphQL
- GraphQL → Python
- GraphQL → TypeScript

### Key Components

#### UnifiedTypeConverter (`type_system_unified/converter.py`)
Main type conversion engine with:
- Configuration-driven mappings loaded from YAML
- Caching layer for performance
- Fallback logic for unmapped types
- Support for complex types (unions, literals, generics, branded types)
- Utility methods (ensure_optional, get_default_value, get_python_imports)

```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter

converter = UnifiedTypeConverter()
python_type = converter.ts_to_python("string[]")  # Returns: List[str]
graphql_type = converter.ts_to_graphql("number")   # Returns: Float
```

#### UnifiedTypeResolver (`type_system_unified/resolver.py`)
Specialized resolver for Strawberry GraphQL field resolution:
- Context-aware field type resolution
- Automatic conversion method generation
- Import statement generation
- Default value handling
- Pydantic decorator detection

```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeResolver

resolver = UnifiedTypeResolver()
resolved = resolver.resolve_field(field_dict, "MyType")
# Returns: ResolvedField with python_type, strawberry_type, conversion_expr, etc.
```

#### TypeRegistry (`type_system_unified/registry.py`)
Runtime type registration system:
- Register custom types, branded types, enums
- Type lookup and validation
- Configuration import/export
- Global registry singleton

```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import get_global_registry

registry = get_global_registry()
registry.register_branded_type("UserID", "str")
registry.register_enum_type("Status", ["pending", "active", "completed"])
```

### Configuration Files

Type mappings are externalized to YAML for easy maintenance:

**`type_mappings.yaml`** - TypeScript → Python conversions:
```yaml
basic_types:
  string: str
  number: float
  boolean: bool

branded_types:
  NodeID: str
  ExecutionID: str

special_fields:
  maxIteration: int
  timeout: int
```

**`graphql_mappings.yaml`** - GraphQL conversions:
```yaml
graphql_to_python:
  String: str
  Int: int
  Float: float
  ID: str

graphql_scalars:
  DateTime: datetime
  JSON: JSON
```

### Usage
```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import (
    UnifiedTypeConverter,
    UnifiedTypeResolver,
    get_global_registry
)

# Type conversion
converter = UnifiedTypeConverter()
python_type = converter.ts_to_python("string[]")

# Field resolution for Strawberry
resolver = UnifiedTypeResolver()
resolved_field = resolver.resolve_field(field_dict, context_type)

# Runtime type registration
registry = get_global_registry()
registry.register_custom_type("MyType", "MyPythonType")
```

### Benefits

1. **Configuration-Driven**: All mappings in YAML, no hardcoded logic
2. **Single Source of Truth**: One converter for all conversions
3. **Well-Tested**: 46 comprehensive tests covering all paths
4. **Extensible**: TypeRegistry for runtime customization
5. **Performance**: Built-in caching for frequently used conversions
6. **Maintainable**: ~40% reduction in type conversion code

### Testing

Run the comprehensive test suite:
```bash
python dipeo/infrastructure/codegen/ir_builders/type_system_unified/test_unified_type_system.py
```

## Best Practices

1. **Always test changes**: Run `make codegen` and verify outputs
2. **Review staged changes**: Use `make diff-staged` before applying
3. **Validate before apply**: Use appropriate validation level (syntax/type/test)
4. **Keep IR snapshots**: Save IR outputs for debugging template issues
5. **Use pipeline for new features**: Extend via steps, not monolithic builders

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors after codegen | Ensure all steps run: parse → codegen → apply → graphql-schema |
| Validation failures | Check test data isn't empty, run with real AST |
| Template errors | Review IR snapshot in `projects/codegen/ir/` |
| Missing dependencies in pipeline | Check step `_dependencies` list |
| Context data not available | Ensure step saves data via `context.set_step_data()` |
| TypeConverter import errors | Use `UnifiedTypeConverter` from `ir_builders/type_system_unified/` |
| Type conversion not working | Check YAML config files in `type_system_unified/` |
| StrawberryTypeResolver not found | Use `UnifiedTypeResolver` from `type_system_unified/` |
