# Code Generation Refactoring Plan

## Overview
Reorganizing `/files/codegen/code/` to follow a top-down approach where each diagram has its own directory with consolidated code.

## New Structure

```
/files/codegen/code/
├── shared/                        # Truly shared utilities across all diagrams
│   ├── ast/                      # AST parsing and caching
│   ├── templates/                # Template environment and filters
│   ├── extractors/               # Common extraction utilities
│   └── writers/                  # Common output writers
│
├── models/                       # Model generation diagrams
│   ├── generate_field_configs/   ✅ DONE (consolidated)
│   ├── generate_python_models/   ✅ DONE (consolidated)
│   ├── generate_graphql_schema/  ✅ DONE (consolidated)
│   ├── generate_conversions/     ✅ DONE (consolidated)
│   ├── generate_enums/           ✅ DONE (consolidated)
│   ├── generate_static_nodes/    ✅ DONE (folder structure)
│   └── parse_all_typescript_batch/ # TODO
│
├── backend/                      # Backend generation diagrams
│   ├── generate_backend/         # TODO
│   └── generate_backend_single_ts/ # TODO
│
├── frontend/                     # Frontend generation diagrams
│   ├── generate_frontend/        # TODO
│   ├── generate_frontend_registry/ # TODO
│   ├── generate_graphql_queries/ # TODO
│   └── generate_zod_schemas/     # TODO
│
└── batch/                        # Batch operations
    ├── generate_all/             # TODO
    └── parse_node_specs_batch/   # TODO
```

## Migration Strategy

### Phase 1: Models (COMPLETED ✅)
- [x] generate_field_configs - Consolidated into single module
- [x] generate_python_models - Consolidated into single module  
- [x] generate_graphql_schema - Consolidated into single module
- [x] generate_conversions - Consolidated into single module
- [x] generate_enums - Consolidated into single module
- [x] generate_static_nodes - Organized into folder structure
- [x] parse_all_typescript_batch - Moved to its own folder
- [x] Cleaned up duplicate files in generators/, extractors/, and utils/

### Phase 2: Frontend
- [ ] generate_frontend
- [ ] generate_frontend_registry
- [ ] generate_graphql_queries
- [ ] generate_zod_schemas

### Phase 3: Backend
- [ ] generate_backend
- [ ] generate_backend_single_ts

### Phase 4: Shared & Batch
- [ ] Move truly shared utilities to shared/
- [ ] Organize batch operations

## Benefits Achieved So Far

1. **Clarity**: Each diagram's code is in one place
2. **Consolidation**: Related functions are grouped together
3. **Maintainability**: Easier to understand and modify
4. **Function reuse**: Diagrams can call multiple functions from same module
5. **Shared utilities**: Common code moved to shared directory
6. **Clean structure**: Removed duplicate files and external dependencies

## Next Steps

Continue with remaining model generation diagrams, then move to frontend and backend.