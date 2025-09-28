# Code Generation Infrastructure

This directory contains the code generation infrastructure that transforms TypeScript specifications into Python backend code, GraphQL schemas, and frontend TypeScript models.

## Architecture Overview

### Core Components

#### IR Builders (`ir_builders/`)
The heart of the code generation system. IR (Intermediate Representation) builders parse TypeScript AST and generate structured data used by templates.

**New Pipeline Architecture (Phase 2)**:
- **`ir_builders/core/`** - Pipeline orchestration framework
  - `context.py` - Build context with caching and configuration
  - `steps.py` - Step interface and pipeline orchestrator
  - `base.py` - Base IR builder using step pipeline

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

**Legacy Components** (to be deprecated):
- `backend_refactored.py`, `frontend.py`, `strawberry_refactored.py` - Old builder implementations
- `backend_extractors.py`, `strawberry_extractors.py` - Legacy extraction logic
- `backend_builders.py`, `strawberry_builders.py` - Legacy assembly logic

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

## Migration Status (Phase 2)

✅ **Completed**:
- Core pipeline infrastructure (`core/`)
- Reusable step modules (`modules/`)
- New pipeline-based builders (`builders/`)
- Validation framework (`validators/`)
- Test harness for compatibility

⏳ **In Progress**:
- Update `ir_registry.py` to use new builders
- Fix minor compatibility issues with empty test data
- Full end-to-end testing with real TypeScript specs

📝 **TODO**:
- Deprecate legacy modules after full validation
- Update documentation in `docs/projects/code-generation-guide.md`
- Add golden fixtures for regression testing

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
