# Code Generation System

Diagram-driven meta-programming using DiPeO itself for code generation ("dog-fooding").

## Architecture

DiPeO diagrams execute to:
- Parse TypeScript AST using typescript_ast nodes
- Build Intermediate Representation (IR) data using ir_builder nodes
- Generate code from IR using template_job nodes

The system now uses DiPeO's native node architecture, with IR building integrated as a first-class node type.

## Structure

```
diagrams/                   # DiPeO diagrams driving generation
ir/                        # Intermediate representation JSON files
templates/                 # Jinja2 templates consuming IR data
dipeo/infrastructure/codegen/ir_builders/  # IR builder implementations
```

## Components

### Core Diagrams
- `generate_all.light.yaml` - Unified parallel generation
- `generate_backend_simplified.light.yaml` - Backend generation from IR
- `generate_frontend_simplified.light.yaml` - Frontend generation from IR
- `generate_strawberry.light.yaml` - GraphQL types & operations from IR

### IR Builder Node Type
The `ir_builder` node type handles IR generation through DiPeO's standard node architecture:
- **Node Spec**: Defined in `dipeo/models/src/nodes/ir-builder.spec.ts`
- **Node Handler**: Implemented in `dipeo/application/execution/handlers/ir_builder.py`
- **IR Implementations**: Located in `dipeo/infrastructure/codegen/ir_builders/`
  - `backend_ir_builder.py` - Consolidates backend models/types
  - `frontend_ir_builder.py` - Extracts frontend components/schemas
  - `strawberry_ir_builder.py` - GraphQL operations & domain types

### IR Data Files
- `backend_ir.json` - Node specs, models, enums
- `frontend_ir.json` - Components, schemas, fields
- `strawberry_ir.json` - GraphQL operations, types, inputs

### Templates
- Jinja2 with custom filters: `ts_to_python`, `pascal_case`, `graphql_field_type`

## Usage

### Workflow
```bash
# 1. Build TypeScript models (after changes)
cd dipeo/models && pnpm build

# 2. Parse TypeScript to regenerate AST cache
make parse-typescript

# 3. Generate code (includes parse-typescript)
make codegen

# 4. Review changes
make diff-staged

# 5. Apply
make apply-test

# 6. Update GraphQL
make graphql-schema
```

### Quick: `make codegen-auto` (DANGEROUS - auto-applies all)

### New Node Type
1. Add TypeScript spec in `dipeo/models/src/node-specs/`
2. Run generation (auto-discovers and updates IR)

### New GraphQL Operation
1. Add definition to `dipeo/models/src/frontend/query-definitions/[entity].ts`
2. Build models: `cd dipeo/models && pnpm build`
3. Run generation to update `strawberry_ir.json`

## Flow

1. **Parse**: TypeScript AST extraction using `typescript_ast` nodes (cached in `temp/`)
2. **Build IR**: Create intermediate representation JSON files using `ir_builder` nodes
3. **Template**: Jinja2 rendering from IR data using `template_job` nodes
4. **Stage**: Output to `diagram_generated_staged/`
5. **Apply**: Move to active directories

The entire flow now executes within DiPeO's native node system, following the standard 3-tier architecture pattern (domain/application/infrastructure).

## Features

- **Native Node Integration**: IR building is now a first-class DiPeO node type
- **IR-Based**: Intermediate representation eliminates duplication
- **Standard Architecture**: Follows DiPeO's 3-tier pattern (domain/application/infrastructure)
- **Node Configuration**: IR builder behavior controlled through node properties
- **Auto-discovery**: Glob patterns find all TypeScript files
- **Batch processing**: Parallel generation with caching
- **AST Cache**: TypeScript parsing cached in `temp/` directory
  - Clear with `make parse-typescript` when models change
  - Automatically cleared when running `make codegen`
- **Type safety**: Single source of truth from TypeScript to Python
- **Unified Operations**: GraphQL operations generated from TypeScript definitions
- **Extensibility**: Add templates/filters without core changes

## Benefits

- **Architectural Consistency**: Uses DiPeO's standard node system instead of external scripts
- **Single Source of Truth**: IR data ensures consistency across all generation targets
- **Enhanced Maintainability**: IR builders follow DiPeO's service patterns and dependency injection
- **Validation**: Proves DiPeO handles complex workflows with native components
- **Efficiency**: 70% less boilerplate, eliminates duplicate extraction logic
- **Configuration Management**: Node properties handle caching and behavior settings
- **Standard Debugging**: Uses DiPeO's built-in logging and error handling
- **Documentation**: Visual diagrams + IR inspection for debugging

## Why Make Over Master Diagrams

- Better error handling (stops on first error)
- Explicit execution flow
- Easier debugging
- Proper file dependencies
- Standard tooling

## Pattern

`AST Parse → Build IR → Template → Output`
- **typescript_ast nodes**: Parse TypeScript and cache AST data
- **ir_builder nodes**: Execute IR builders from `dipeo/infrastructure/codegen/ir_builders/`
- **template_job nodes**: Consume IR data for consistent generation
- All components follow DiPeO's standard node architecture patterns

## Best Practices

1. **Cache First**: Check/create AST cache using typescript_ast nodes
2. **Build IR**: Always regenerate IR when TypeScript changes using ir_builder nodes
3. **Inspect IR**: Check `ir/*.json` files for debugging
4. **Validate Staged**: Test before applying
5. **Template Filters**: Use for type conversions in template_job nodes
6. **Batch Operations**: Group for efficiency
7. **Node Configuration**: Configure IR builder behavior through node properties
8. **Standard Architecture**: IR builders follow DiPeO's 3-tier pattern in `dipeo/infrastructure/codegen/`

See [Light Diagram Guide](../../docs/formats/comprehensive_light_diagram_guide.md)
