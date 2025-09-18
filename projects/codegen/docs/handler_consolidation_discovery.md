# Codegen Handler Consolidation - Phase 1 Discovery Report

## Executive Summary

This document catalogues the four code-generation oriented handlers (`template_job`, `typescript_ast`, `ir_builder`, `json_schema_validator`) and proposes a unified `codegen` package architecture that mirrors existing complex handler patterns while maintaining backward compatibility.

## Handler Analysis

### 1. TemplateJobNodeHandler

**Location**: `dipeo/application/execution/handlers/template_job.py`

**Purpose**: Renders Jinja2 templates with variable substitution and file output

**Entry Points**:
- Registered in `handler_factory.py` via `@register_handler` decorator
- Node type: `NodeType.TEMPLATE_JOB`
- Used in 6 codegen diagrams for code generation

**Inputs**:
- `template_path` or `template_content`: Template source
- `variables`: Template context variables
- `output_path`: Where to write rendered output
- `engine`: Template engine (internal/jinja2)
- `preprocessor`: Optional module/function for context enrichment
- Envelope inputs from connected nodes

**Outputs**:
- Rendered template string
- Written file (if output_path specified)
- Envelope with metadata (engine, template_path, output_path, template_vars)

**Services Used**:
- `FILESYSTEM_ADAPTER`: File I/O operations
- `TEMPLATE_RENDERER`: Jinja2 rendering service

**Key Features**:
- Deduplication logic for preventing duplicate writes
- Preprocessor support for dynamic context modification
- Template path resolution using Jinja2
- Batch/foreach mode support (partially implemented)

### 2. TypescriptAstNodeHandler

**Location**: `dipeo/application/execution/handlers/typescript_ast.py`

**Purpose**: Parses TypeScript source code and extracts AST, interfaces, types, and enums

**Entry Points**:
- Registered via `@register_handler` decorator
- Node type: `NodeType.TYPESCRIPT_AST`
- Used in parse_typescript_batch_direct diagram

**Inputs**:
- `source`: TypeScript source code (single mode)
- `sources`: Dictionary of file paths to source code (batch mode)
- `extract_patterns`: What to extract (interface, type, enum, class, function, const, export)
- `parse_mode`: module or script
- `include_js_doc`: Include JSDoc comments
- `batch`: Enable batch processing
- `batchInputKey`: Key for batch input data

**Outputs**:
- Extracted AST data with interfaces, types, enums
- Metadata (extractedCount, byType)
- Envelope with batch_mode flag and statistics

**Services Used**:
- `AST_PARSER`: TypeScript parsing service

**Key Features**:
- Single and batch mode processing
- Cache skip detection (_skip_parsing flag)
- Flexible input discovery (supports various input structures)
- JSDoc extraction support

### 3. IrBuilderNodeHandler

**Location**: `dipeo/application/execution/handlers/ir_builder.py`

**Purpose**: Builds intermediate representation (IR) from parsed source data

**Entry Points**:
- Registered via `@register_handler` decorator
- Node type: `NodeType.IR_BUILDER`
- Used in generate_backend_simplified and generate_frontend_simplified diagrams

**Inputs**:
- Source data from TypeScript AST parsing (via envelope)
- `builder_type`: Type of IR builder (backend, frontend, strawberry)
- `output_format`: json, yaml, or raw
- `cache_enabled`: Enable caching
- `validate_output`: Validate IR after building

**Outputs**:
- IR data (merged data + metadata for json/yaml format)
- Raw IRData structure (for raw format)
- Envelope with builder metadata

**Services Used**:
- `IR_CACHE`: Caching service for IR data
- `IR_BUILDER_REGISTRY`: Registry of available IR builders

**Key Features**:
- Multiple builder types (backend, frontend, strawberry)
- Cache management with key generation
- Output format transformation
- Validation support

### 4. JsonSchemaValidatorNodeHandler

**Location**: `dipeo/application/execution/handlers/json_schema_validator.py`

**Purpose**: Validates JSON data against JSON Schema specifications

**Entry Points**:
- Registered via `@register_handler` decorator
- Node type: `NodeType.JSON_SCHEMA_VALIDATOR`
- Not currently used in codegen diagrams

**Inputs**:
- `schema_path` or `json_schema`: Schema specification
- `data_path` or envelope input: Data to validate
- `strict_mode`: Validate all errors
- `error_on_extra`: Reject additional properties

**Outputs**:
- Validated data (on success)
- Validation errors (on failure)
- Envelope with validation metadata

**Services Used**:
- `FILESYSTEM_ADAPTER`: File I/O for schema/data files

**Key Features**:
- Flexible schema/data input (file or inline)
- Strict mode validation
- Additional properties handling
- Detailed error reporting

## Shared Functionality Analysis

### Common Patterns

1. **Service Injection**:
   - All handlers use `@requires_services` decorator
   - Services accessed via `self._service_name` pattern
   - Common services: FILESYSTEM_ADAPTER

2. **Envelope Communication**:
   - All handlers return Envelope objects
   - Use EnvelopeFactory for creation
   - Include metadata in envelopes

3. **Input Processing**:
   - `prepare_inputs()` method for envelope conversion
   - Support for both node properties and envelope inputs
   - Flexible input discovery patterns

4. **Lifecycle Hooks**:
   - `validate()`: Compile-time validation
   - `pre_execute()`: Runtime setup
   - `run()`: Core execution logic
   - `serialize_output()`: Envelope creation
   - `post_execute()`: Token emission

5. **Error Handling**:
   - Validation errors in validate()
   - Runtime errors as error envelopes
   - Detailed error messages with context

### Shared Utilities

1. **Template Processing**:
   - Jinja2 rendering (template_job, used by others indirectly)
   - Variable resolution and context building

2. **File Operations**:
   - Path resolution (absolute/relative)
   - Directory creation
   - Glob pattern matching

3. **Data Transformation**:
   - JSON serialization/deserialization
   - Format conversion (json/yaml/raw)
   - Metadata extraction

4. **Caching**:
   - Cache key generation (ir_builder)
   - Deduplication (template_job)
   - Skip detection (typescript_ast)

## Proposed Codegen Package Structure

**Important Architecture Note**: Each handler already properly uses infrastructure services (TEMPLATE_RENDERER, AST_PARSER, IR_BUILDER_REGISTRY, etc.). We should NOT create duplicate service layers.

```
dipeo/application/execution/handlers/codegen/
├── __init__.py                 # Package initialization and exports
├── base.py                      # BaseCodegenHandler (ONLY shared handler patterns)
├── template.py                  # TemplateJobNodeHandler
├── typescript_ast.py            # TypescriptAstNodeHandler
├── ir_builder.py               # IrBuilderNodeHandler
└── schema_validator.py         # JsonSchemaValidatorNodeHandler
```

**Why this minimal structure?**
- Handlers already delegate to proper infrastructure services
- No need for utils/services that would duplicate existing layers
- Grouping provides organizational clarity without over-abstraction
- Maintains clean architecture boundaries

## Common Interfaces

```python
# base.py
class BaseCodegenHandler(TypedNodeHandler):
    """Base handler for HANDLER PATTERNS ONLY - services remain in infrastructure."""

    def extract_envelope_body(self, inputs: dict[str, Envelope]) -> dict:
        """Common pattern for extracting data from envelope inputs.
        Used by all handlers to unwrap 'default' and other patterns."""

    def detect_batch_mode(self, node: BaseModel, inputs: dict) -> tuple[bool, dict]:
        """Common batch detection logic.
        Returns (is_batch, batch_data)."""

    def build_standard_metadata(self, node: BaseModel, **extra) -> dict:
        """Consistent metadata structure for envelopes."""

    # Note: NO file operations, caching, or rendering here
    # Those belong to infrastructure services
```

## Why No Orchestrator?

The diagrams already orchestrate by connecting nodes. An orchestrator class would duplicate what DiPeO's execution engine already does. If complex workflows are needed, they should be:
1. Expressed as diagrams (dog-fooding)
2. Or added to the execution engine itself

## Backward Compatibility Strategy

### Simple Import Redirect

Since we're just reorganizing (not changing functionality), compatibility is trivial:

```python
# dipeo/application/execution/handlers/__init__.py
# Import from new location but expose at old location
from .codegen.template import TemplateJobNodeHandler
from .codegen.typescript_ast import TypescriptAstNodeHandler
from .codegen.ir_builder import IrBuilderNodeHandler
from .codegen.schema_validator import JsonSchemaValidatorNodeHandler

# handler_factory.py continues to work unchanged
```

### Migration Steps

1. Move handlers to `codegen/` package
2. Update `handlers/__init__.py` to re-export from new location
3. handler_factory.py continues to import as before
4. Zero changes needed to diagrams or external code
```

## Benefits of Consolidation

1. **Organizational Clarity**: Groups related handlers in one package
2. **Reduced Duplication**: ~10-15% reduction from shared handler patterns (not 40%)
3. **Easier Navigation**: Clear that these handlers work together for codegen
4. **Maintains Architecture**: Respects existing service boundaries
5. **Zero Breaking Changes**: Simple reorganization with import redirects
6. **Documentation**: One place to understand all codegen operations

## Migration Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing diagrams | Facade pattern maintains compatibility |
| Service dependency changes | Keep same service keys and interfaces |
| Performance regression | Benchmark before/after, optimize hot paths |
| Lost functionality | Comprehensive test coverage before migration |
| Complex debugging | Enhanced logging and tracing in new structure |

## Recommendations

1. **Keep it Simple**: Just reorganize, don't reinvent
2. **Extract Carefully**: Only truly shared handler patterns go in base class
3. **Respect Boundaries**: Services stay in infrastructure/domain layers
4. **Test Import Paths**: Ensure backward compatibility works
5. **Document Purpose**: Clear that this is organizational, not architectural

## Next Steps (Phase 2)

1. Create `codegen/` package directory
2. Move handlers to new location (minimal changes)
3. Extract truly shared patterns to `base.py` (if any)
4. Update imports in `handlers/__init__.py`
5. Test that all diagrams still work
6. Document the organization in package `__init__.py`

## Open Questions (Resolved)

1. **Single configurable node vs multiple types?**
   - **Answer**: Keep multiple types for clarity, use orchestrator for coordination

2. **Staging migration for external diagrams?**
   - **Answer**: Use facades for 100% compatibility, deprecate gradually

3. **Runtime feature flags?**
   - **Answer**: Not needed with facade pattern, can add if issues arise

## Conclusion

The consolidation should be primarily **organizational**, not architectural. The handlers are already well-designed and properly use infrastructure services.

Key insights:
- **Architecture is sound**: Each handler correctly delegates to infrastructure services
- **Minimal duplication**: Only 10-15% shared patterns (envelope processing, batch detection)
- **Simple is better**: Just group related handlers, don't create unnecessary abstractions
- **Respect boundaries**: Services belong in infrastructure/domain, not application handlers

The real value is **clarity**: developers will immediately understand these handlers work together for code generation. This is similar to how `person_job/` groups conversation-related handlers, but simpler because codegen handlers need less coordination.

This minimal approach maintains DiPeO's clean architecture while improving code organization with zero breaking changes.
