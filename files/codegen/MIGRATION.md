# Code Generation Migration Guide

## Overview

DiPeO is migrating from a legacy TypeScript-based code generation system to a fully diagram-based approach where DiPeO uses itself to generate all code. This migration covers two distinct generation systems:

1. **Node Specification Generation** - Generates UI components and backend models from JSON specifications
2. **Domain Model Generation** - Generates core Python models and utilities from TypeScript domain models

### Key Distinction

- **Node Specifications** define individual node types (like `person_job`, `api_job`) - their properties, UI fields, and behavior
- **Domain Models** define core data structures used throughout DiPeO (like `Diagram`, `Node`, `Execution`, `Arrow`)

Both systems generate code from TypeScript sources, but serve different purposes in the architecture.

## Current Code Generation Systems

### 1. Node Specification Generation (Mostly Migrated)
Generates from `files/codegen/specifications/nodes/*.json`:
- Frontend: `apps/web/src/__generated__/models/*Node.ts` (TypeScript models + Zod schemas)
- Frontend: `apps/web/src/__generated__/fields/*Fields.ts` (Field configurations)
- Frontend: `apps/web/src/__generated__/nodes/*Config.ts` (Node configurations)
- Backend: `dipeo/diagram_generated/models/*_model.py` (Pydantic models)
- Backend: `dipeo/diagram_generated/graphql/*_schema.graphql` (GraphQL schemas)

### 2. Domain Model Generation (In Migration)
Generates from `dipeo/models/src/*.ts`:
- `dipeo/models/models.py` - Core Python domain models
- `dipeo/models/conversions.py` - TypeScript to Python type conversions
- `apps/web/src/__generated__/nodes/fields.ts` - Unified field configurations
- `dipeo/models/dist/generated/zod_schemas.js` - Zod validation schemas
- Various GraphQL and utility files

## Migration Status

### ✅ Completed
#### Node Specification Generation
- TypeScript specification types defined (`dipeo/models/src/node-specifications.ts`)
- All 15 node types migrated to TypeScript specifications
- TypeScript parsing diagram created (`shared/parse_typescript_specs.light.yaml`)
- Frontend generation updated to use TypeScript (`generate_frontend_single_ts.light.yaml`)
- Frontend batch generation created for TypeScript (`generate_frontend_batch_ts.light.yaml`)
- Backend generation updated to use TypeScript (`generate_backend_single_ts.light.yaml`)
- Backend batch generation created for TypeScript (`generate_backend_batch_ts.light.yaml`)
- Unified generation pipeline created and replaced legacy `generate_all.light.yaml`
- Fixed TypeScript parser to handle enum references and complex object literals
- Fixed field config template to properly generate nested fields with uiConfig
- Added support for 'group' field type in TypeScript definitions
- Fixed manifest node naming issues (`example_hook` → `hook`, `typescript_ast_parser` → `typescript_ast`)
- Removed old JSON specification files from `files/codegen/specifications/nodes/`
- Resolved string vs dict error in field_config.py (was caused by incorrect node names in manifest)

#### Domain Model Generation
- Python domain model generation diagram (`generate_python_models.light.yaml`)
- Python model generator module (`files/codegen/code/models/generators/python_models.py`)
- Python model template (`files/codegen/templates/models/python_models.j2`)

### 🚧 In Progress
- Testing and debugging the complete generation pipeline
- Updating master generation diagram to use TypeScript batch generation

### 📋 TODO

#### Immediate Fixes
- Update master generation diagram to use TypeScript batch generation

#### Domain Model Generation Diagrams
- Create diagram for conversions generation (`models/generate_conversions.light.yaml`)
- Create diagram for field configs generation (`models/generate_field_configs.light.yaml`)
- Create diagram for Zod schemas generation (`models/generate_zod_schemas.light.yaml`)
- Create diagram for GraphQL schema generation (`models/generate_graphql_schema.light.yaml`)
- Create diagram for static nodes generation (`models/generate_static_nodes.light.yaml`)

#### Integration
- Update Makefile to use diagram-based generation instead of legacy scripts
- Create master diagram for domain model generation (`models/generate_all_models.light.yaml`)
- ✅ Updated `generate_all.light.yaml` to use existing `generate_all_models` sub-diagram
- Deprecate and remove legacy TypeScript scripts
- Update documentation
- Remove old JSON specification files from `files/codegen/specifications/nodes/`

## Issue Resolution Summary

### String vs Dict Error in field_config.py
**Root Cause**: The manifest file (`all.json`) contained incorrect node names that didn't match the TypeScript specification filenames:
- `example_hook` should have been `hook` (matching `hook.spec.ts`)
- `typescript_ast_parser` should have been `typescript_ast` (matching `typescript-ast.spec.ts`)

**Solution**: Updated the manifest to use correct node names, ensuring the file loader can find the corresponding TypeScript specification files.

### Empty/Corrupted Node Generation Output
**Root Cause**: When the TypeScript specification file couldn't be found (due to naming mismatch), the generation would fail but still create output files with error messages or template placeholders like `{node_naming.node_name}Fields.ts`.

**Solution**: Fixed node names in manifest and cleaned up corrupted files. All nodes now generate correctly.

## New Architecture

### 1. Single Source of Truth
All definitions are now in TypeScript:
- **Domain models**: `dipeo/models/src/*.ts` (Core data structures: Diagram, Node, Execution, etc.)
- **Node specifications**: `dipeo/models/src/node-specs/*.spec.ts` (Individual node type definitions)

### 2. Diagram-Based Generation
Everything is generated using DiPeO diagrams:
```
TypeScript Sources → DiPeO Diagrams → Generated Code
```

### 3. Key Generation Diagrams

#### Node Specification Generation
- `frontend/generate_frontend_single.light.yaml` - Single frontend component
- `frontend/generate_frontend_batch.light.yaml` - Batch frontend generation
- `backend/generate_backend_single.light.yaml` - Single backend model
- `backend/generate_backend_batch_ts.light.yaml` - Batch backend generation from TypeScript
- `generate_all.light.yaml` - Complete unified generation pipeline (both domain models and node specs)

#### Domain Model Generation (Being Created)
- `models/generate_python_models.light.yaml` - Python domain models
- `models/generate_conversions.light.yaml` - Type conversions (TODO)
- `models/generate_field_configs.light.yaml` - Field configurations (TODO)
- `models/generate_zod_schemas.light.yaml` - Zod validation schemas (TODO)
- `models/generate_graphql_schema.light.yaml` - GraphQL schema (TODO)

#### Master Orchestrator
- `generate_all.light.yaml` - Runs both node spec and domain model generation (unified pipeline)

## Usage

### Current Commands (Legacy TypeScript-based)
```bash
# Generate all domain models and node specifications
make codegen

# Generate domain models only
make codegen-models
```

### New Diagram-Based Commands

#### Node Specification Generation
```bash
# Generate all code (domain models + node specs)
dipeo run codegen/diagrams/generate_all --light --debug --no-browser --timeout=30

# Generate single node frontend from TypeScript
dipeo run codegen/diagrams/frontend/generate_frontend_single_ts --light --debug --no-browser \
  --input-data '{"node_spec_path": "person_job"}'

# Generate all frontend nodes from TypeScript
dipeo run codegen/diagrams/frontend/generate_frontend_batch_ts --light --debug --no-browser --timeout=60

# Generate all backend nodes from TypeScript
dipeo run codegen/diagrams/backend/generate_backend_batch_ts --light --debug --no-browser --timeout=60
```

#### Domain Model Generation (In Development)
```bash
# Generate Python domain models
dipeo run codegen/diagrams/models/generate_python_models --light --debug --no-browser

# Other domain model generation diagrams coming soon...
```

## Migrating a Node Specification

1. Create TypeScript specification in `dipeo/models/src/node-specs/{node-name}.spec.ts`
2. Export it from `dipeo/models/src/node-specs/index.ts`
3. Remove the JSON file from `files/codegen/specifications/nodes/`
4. Test generation: `make codegen`

## Benefits

1. **Type Safety**: Node specifications are type-checked
2. **Better IDE Support**: Auto-completion, refactoring, go-to-definition
3. **Single Source**: No more JSON/TypeScript split
4. **Dogfooding**: DiPeO generates itself
5. **Visual Debugging**: See generation flow in diagram editor
6. **Parallelization**: Leverage DiPeO's execution engine

## Technical Details

### TypeScript Parsing
The `typescript_ast` node parses TypeScript files and extracts:
- Interfaces
- Type aliases
- Enums
- Constants
- JSDoc comments

### Template System
Jinja2 templates are used for code generation:
- Located in `files/codegen/templates/`
- Support custom filters for case conversion
- Maintain consistent code style

### Generation Flow
1. Parse TypeScript sources
2. Extract specifications and models
3. Apply templates
4. Write generated files
5. Update registries

## Troubleshooting

### Node not appearing in UI
1. Check TypeScript specification is exported
2. Verify generation completed without errors
3. Ensure `NodeType` enum includes the node

### Generation errors
1. Check TypeScript syntax
2. Verify all required fields in specification
3. Look for errors in diagram execution logs

### Type mismatches
1. Ensure TypeScript types match expected formats
2. Check field type mappings
3. Verify enum values are consistent