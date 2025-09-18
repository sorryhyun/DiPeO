# Codegen Handler Package

This package consolidates code-generation oriented handlers for organizational clarity.

## Purpose

Groups related handlers that work together for code generation operations. This is **purely organizational** - the architecture and functionality remain unchanged.

## Structure

```
codegen/
├── __init__.py                 # Package initialization and exports
├── base.py                      # Minimal shared handler patterns
├── template.py                  # TemplateJobNodeHandler - Jinja2 template rendering
├── typescript_ast.py            # TypescriptAstNodeHandler - TypeScript parsing
├── ir_builder.py               # IrBuilderNodeHandler - IR generation
└── schema_validator.py         # JsonSchemaValidatorNodeHandler - JSON schema validation
```

## Architecture Notes

- **Services stay in infrastructure**: Each handler uses infrastructure services (TEMPLATE_RENDERER, AST_PARSER, etc.)
- **No duplicate functionality**: Base class contains only handler patterns, not service logic
- **Backward compatible**: All imports redirected through `handlers/__init__.py`
- **Zero breaking changes**: Simple reorganization with import redirects

## Handler Descriptions

### TemplateJobNodeHandler (`template.py`)
- Renders Jinja2 templates with variable substitution
- Supports preprocessors and deduplication
- Uses TEMPLATE_RENDERER service from infrastructure

### TypescriptAstNodeHandler (`typescript_ast.py`)
- Parses TypeScript source code and extracts AST
- Supports batch processing and caching
- Uses AST_PARSER service from infrastructure

### IrBuilderNodeHandler (`ir_builder.py`)
- Builds intermediate representation from parsed data
- Supports multiple builder types (backend, frontend, strawberry)
- Uses IR_BUILDER_REGISTRY and IR_CACHE services

### JsonSchemaValidatorNodeHandler (`schema_validator.py`)
- Validates JSON data against schemas
- Supports strict mode and additional property validation
- Uses FILESYSTEM_ADAPTER for file operations

## Base Class

The `BaseCodegenHandler` provides minimal shared patterns:
- `extract_envelope_body()` - Common envelope unwrapping
- `extract_envelope_inputs()` - Multiple envelope extraction
- `detect_batch_mode()` - Batch processing detection
- `build_standard_metadata()` - Consistent metadata structure

These are **handler patterns only** - actual functionality remains in infrastructure services.

## Usage

All handlers are auto-registered via the `@register_handler` decorator and can be imported from either location:

```python
# New location (internal use)
from dipeo.application.execution.handlers.codegen.template import TemplateJobNodeHandler

# Original location (backward compatibility)
from dipeo.application.execution.handlers import TemplateJobNodeHandler
```

## Benefits

1. **Organizational Clarity**: Clear that these handlers work together
2. **Reduced Duplication**: ~10-15% reduction from shared patterns
3. **Easier Navigation**: Related code grouped together
4. **Maintains Architecture**: Respects service boundaries
5. **Zero Breaking Changes**: Complete backward compatibility

## Migration

This consolidation involved:
1. Creating the `codegen/` package
2. Moving handlers with minimal changes
3. Extracting truly shared patterns to base class
4. Updating imports for backward compatibility

No changes required for:
- Existing diagrams
- External code
- Service implementations
- Infrastructure layer

This follows the same pattern as other complex handlers like `person_job/` and `sub_diagram/` but simpler since codegen handlers need less coordination.
