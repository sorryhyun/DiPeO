# Model Code Generation Structure

This directory contains code generators for model-related diagrams. Each diagram has its own subdirectory with consolidated code.

## Directory Structure

```
models/
├── generate_field_configs/        # Field configuration generation (consolidated)
├── generate_python_models/        # Python domain model generation (consolidated)
├── generate_graphql_schema/       # GraphQL schema generation (consolidated)
├── generate_conversions/          # Conversions generation (consolidated)
├── generate_enums/                # Enum generation (consolidated)
├── generate_static_nodes/         # Static node generation (folder structure)
├── parse_all_typescript_batch/    # TypeScript parsing and caching
│
├── extractors/                    # Shared extractors still in use
│   ├── static_nodes_extractor.py  # Used by generate_static_nodes
│   └── zod_schemas_extractor.py   # Used by frontend generation
│
├── generators/                    # Remaining shared generators
│   ├── json_schema_generator.py   # Used by generate_validation_models
│   ├── pydantic_generator.py      # Used by generate_validation_models
│   └── summary_generator.py       # Used by multiple diagrams
│
├── utils/                         # Shared utilities
│   └── ast_cache.py               # AST caching utilities
│
└── writers/                       # Output writers
    └── json_writer.py             # JSON file writing
```

## Key Benefits

1. **Clear ownership**: Each diagram owns its code in one place
2. **Easy navigation**: Find code by diagram name
3. **Function reuse**: Multiple nodes can call different functions from the same module
4. **Reduced file sprawl**: Consolidates related logic

## Function Naming Convention

Each generator module exports functions that correspond to diagram nodes:
- Main processing functions (e.g., `extract_field_configs`, `generate_python_models`)
- Template preparation functions (e.g., `prepare_template_data`)
- Rendering functions (e.g., `render_field_configs`)
- Summary generation functions (e.g., `generate_summary`)

## Backward Compatibility

Each module maintains aliases for backward compatibility:
- `main` - Usually points to the primary function
- Original function names are preserved where possible