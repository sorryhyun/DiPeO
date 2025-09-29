# Code Generation Guide

## Overview

DiPeO uses a diagram-driven, IR-based (Intermediate Representation) code generation pipeline that "dog-foods" its own execution engine. All code generation is orchestrated through DiPeO diagrams, maintaining type safety from TypeScript node specifications to GraphQL queries and Python handlers.

**Key Philosophy**: DiPeO uses itself to build itself - all code generation runs through DiPeO diagrams, proving the platform's maturity and capabilities.

**IR-Based Architecture**: The system now uses intermediate representation JSON files as a single source of truth, eliminating duplication and centralizing extraction logic in dedicated IR builders.

## Generation Flow

```
1. Node Specifications (TypeScript in /dipeo/models/src/)
   ↓
2. Run generate_all diagram (dipeo run codegen/diagrams/generate_all)
   ├─→ Parse TypeScript → Cache AST in /temp/*.json
   ├─→ Build IR → backend_ir.json, frontend_ir.json, strawberry_ir.json
   ├─→ Generate from IR → Domain Models → /dipeo/diagram_generated_staged/
   └─→ Generate from IR → Frontend Code → /apps/web/src/__generated__/
   ↓
3. Verify staged code in /dipeo/diagram_generated_staged/
   ↓
4. Apply Staged Changes (make apply-test)
   ↓
5. Export GraphQL Schema → /apps/server/schema.graphql
   ↓
6. Generate TypeScript Types (pnpm codegen)
```

**Key Features**:
- **IR-Based**: Intermediate representation JSON files eliminate duplication
- **Unified Generation**: Single `generate_all` diagram handles models, frontend, and GraphQL in parallel
- **Staging Directory**: Changes preview in `/dipeo/diagram_generated_staged/` before applying
- **Dynamic Discovery**: Automatically finds all TypeScript files using glob patterns
- **External Code**: IR builders and generators in `projects/codegen/code/` for reusability
- **Syntax Validation**: Default validation ensures generated code is syntactically correct
- **Single Source of Truth**: TypeScript → IR → Generated code ensures consistency

### Stage 1: TypeScript Parsing & Caching

**Source**: All TypeScript files in `/dipeo/models/src/`
**Cache**: `/temp/*.json` (AST JSON files)
**Diagram**: `codegen/diagrams/parse_typescript_batch_direct.light.yaml`

The system automatically discovers and parses all TypeScript files, caching their AST for subsequent IR building.

### Stage 2: Build Intermediate Representation

**Source**: Cached AST files
**IR Builders**:
- `backend_ir_builder.py` → `backend_ir.json` (node specs, models, enums)
- `frontend_ir_builder.py` → `frontend_ir.json` (components, schemas, fields)
- `strawberry_ir_builder.py` → `strawberry_ir.json` (GraphQL operations, types)

### Stage 3: Unified Code Generation from IR

**Source**: IR JSON files
**Diagrams**:
- `generate_backend_simplified.light.yaml` - Backend generation from IR
- `generate_frontend_simplified.light.yaml` - Frontend generation from IR
- `generate_strawberry.light.yaml` - GraphQL types & operations from IR

**Outputs**:
- Domain models → `/dipeo/diagram_generated_staged/`
- Frontend code → `/apps/web/src/__generated__/`

The `generate_all` diagram orchestrates all generation in parallel:

**Domain Models** (to staging):
- Pydantic models (`/models/`)
- Enums (`/enums/`)
- Validation models (`/validation/`)
- GraphQL schema templates
- Strawberry types and mutations
- Static node classes
- Type conversions

**Frontend Components** (direct output):
- Field configurations (`/fields/`)
- Node models and configs (`/models/`, `/nodes/`)
- GraphQL queries (`/queries/*.graphql`)
- Zod validation schemas
- Frontend registry

### Stage 4: Apply Staged Changes

**Action**: Manual copy from `/dipeo/diagram_generated_staged/` → `/dipeo/diagram_generated/`  
**Validation**: Syntax-only by default (Python compilation check)

Use `make apply-test` to move staged backend code to active directory. This ensures:
- Validated code before activation
- Ability to review changes before applying
- Rollback safety if generation has issues

### Stage 5: Export GraphQL Schema

**Command**: `make graphql-schema`  
**Output**: `/apps/server/schema.graphql`

Exports the complete GraphQL schema from the application layer, capturing all types and operations from the generated Strawberry types.

### Stage 6: GraphQL TypeScript Generation

**Source**: `/apps/web/src/__generated__/queries/*.graphql` + `/apps/server/schema.graphql`  
**Output**: `/apps/web/src/__generated__/graphql.tsx`  
**Command**: Automatic via `pnpm codegen`

Generates fully typed:
- TypeScript types for all GraphQL operations
- React hooks (useQuery, useMutation, useSubscription)
- Apollo Client integration code

## Commands

### Recommended Workflow

```bash
# Step 1: Build TypeScript models (if changed)
cd dipeo/models && pnpm build

# Step 2: Generate all code with IR (models + frontend)
make codegen               # Includes parse-typescript automatically

# Step 3: Verify staged changes and IR
make diff-staged           # Compare staged vs active files
ls -la projects/codegen/ir/  # Inspect IR files if needed

# Step 4: Apply staged backend code
make apply-test                 # Apply with full mypy type checking

# Step 5: Update GraphQL schema and types
make graphql-schema        # Export schema and generate TypeScript types
```

### Quick Commands

```bash
make codegen-auto         # DANGEROUS: Runs generate_all + auto-apply + GraphQL schema
make codegen-watch        # Watch TypeScript files for changes
```

### Staging Commands

```bash
make diff-staged           # Compare staged vs active generated files
make validate-staged       # Full validation with mypy type checking
make validate-staged-syntax # Syntax validation only (faster)
make apply                 # Apply with full validation
make apply-test            # Apply with syntax validation only
make backup-generated      # Backup before applying changes
```

### Direct Diagram Execution (Advanced)

```bash
# Generate everything (models + frontend)
dipeo run codegen/diagrams/generate_all --light --debug

# Generate specific node (for debugging)
dipeo run codegen/diagrams/models/generate_backend_models_single --light \
  --input-data '{"node_name": "person_job"}'

# Rebuild IR only (useful for debugging)
dipeo run codegen/diagrams/generate_backend_simplified --light --debug
```

## Dog-fooding Architecture

DiPeO's code generation exemplifies "dog-fooding" - using DiPeO diagrams to generate DiPeO's own code:

1. **Visual Programming**: Each generation step is a diagram node
2. **IR-Based Design**: Centralized intermediate representation for consistency
3. **Composability**: Sub-diagrams handle specific generation tasks
4. **Parallelization**: Batch processing for multiple files
5. **Error Handling**: Graceful degradation in batch operations
6. **Caching**: AST parsing cached, IR files for debugging

This approach proves DiPeO's maturity - the platform is robust enough to build itself using sophisticated IR-based meta-programming.

## Why The Staging Approach Matters

The staging directory (`diagram_generated_staged`) serves critical purposes:

1. **Preview Changes**: Review generated code before applying
2. **Atomic Updates**: All-or-nothing application of changes
3. **Syntax Validation**: Catch errors before they break the system
4. **Rollback Safety**: Easy to discard bad generations
5. **Frontend Dependency**: Frontend reads from applied (not staged) models

## Adding New Features

### Adding a New Node Type

1. **Create node specification**:
   ```typescript
   // /dipeo/models/src/node-specs/my-node.spec.ts
   export const myNodeSpec: NodeSpecification = {
     nodeType: NodeType.MyNode,
     category: 'processing',
     displayName: 'My Node',
     icon: 'Code',
     fields: [
       {
         name: 'myField',
         type: 'string',
         required: true,
         description: 'Description of the field',
         uiType: 'text',  // UI hint for frontend
         placeholder: 'Enter value...'
       }
     ]
   };
   ```

2. **Create Python handler**:
   ```python
   # /dipeo/application/execution/handlers/my_node.py
   from dipeo.diagram_generated.models.my_node import MyNodeData
   from dipeo.application.execution.handlers.base import TypedNodeHandler
   from dipeo.domain.base.mixins import LoggingMixin, ValidationMixin
   
   @register_handler
   class MyNodeHandler(TypedNodeHandler[MyNodeData], LoggingMixin, ValidationMixin):
       def prepare_inputs(self, inputs: dict, request: ExecutionRequest) -> dict:
           # Transform raw inputs
       
       async def run(self, inputs: dict, request: ExecutionRequest) -> Any:
           # Implementation using mixins for logging/validation
       
       def serialize_output(self, result: Any, request: ExecutionRequest) -> Envelope:
           # Convert to Envelope
   ```

3. **Run code generation**:
   ```bash
   # Build TypeScript if changed
   cd dipeo/models && pnpm build

   # Generate all code with the new node (rebuilds IR)
   make codegen

   # Apply staged changes
   make apply-test

   # Update GraphQL schema
   make graphql-schema
   ```

4. **The node is now available** with:
   - Full type safety across Python and TypeScript
   - Auto-generated UI components
   - GraphQL types and operations
   - Validation schemas

### Handler Scaffolding

When adding new node types, DiPeO can automatically generate handler stubs to jumpstart backend implementation:

1. **Add handler metadata to your node spec**:
   ```typescript
   // In /dipeo/models/src/nodes/my-node.spec.ts
   export const myNodeSpec: NodeSpecification = {
     // ... other fields ...

     handlerMetadata: {
       modulePath: "dipeo.application.execution.handlers.my_node",
       className: "MyNodeHandler",
       mixins: ["LoggingMixin", "ValidationMixin"],
       serviceKeys: ["LLM_CLIENT", "STATE_STORE"],
       skipGeneration: false,  // Set to true for custom handlers
       customImports: []       // Additional imports if needed
     }
   };
   ```

2. **Run code generation**:
   ```bash
   cd dipeo/models && pnpm build
   make codegen
   ```

3. **Review generated handler stub**:
   - Location: `/dipeo/diagram_generated_staged/handlers/my-node_handler.py`
   - Includes proper imports, mixins, service declarations
   - Contains TODO markers for implementation
   - Preserves existing handlers (won't overwrite)

4. **Handler metadata fields**:
   - `modulePath`: Python module path for the handler
   - `className`: Handler class name
   - `mixins`: Service mixins to include (e.g., LoggingMixin)
   - `serviceKeys`: Required services (e.g., LLM_CLIENT, EVENT_BUS)
   - `skipGeneration`: Skip stub generation for custom handlers
   - `customImports`: Additional import statements needed

5. **Generated handler includes**:
   - Proper class inheritance with mixins
   - Type hints using the node's data model
   - Service key declarations
   - Envelope pattern implementation
   - Examples for common service usage

### Adding New GraphQL Queries/Mutations

1. **For existing entities**, modify the query generator:
   ```python
   # /projects/codegen/code/frontend/generators/query_generator_dipeo.py
   # In generate_diagram_queries() or similar method
   # Note: Uses snake_case internally with Pydantic aliases for GraphQL compatibility
   
   queries.append("""query MyNewQuery($id: ID!) {
     diagram(id: $id) {
       # Add fields (camelCase in GraphQL, snake_case in Python)
     }
   }""")
   ```

2. **For new entities**, create a new query generator:
   ```python
   # /projects/codegen/code/frontend/queries/my_entity_queries.py
   class MyEntityQueryGenerator:
       def generate(self) -> List[str]:
           return [
               """query GetMyEntity($id: ID!) {
                 myEntity(id: $id) {
                   id
                   name
                 }
               }"""
           ]
   ```

3. **Register in main generator**:
   ```python
   # In DiPeOQueryGenerator.generate_all_queries()
   my_entity_generator = MyEntityQueryGenerator()
   self.write_query_file('myEntity', my_entity_generator.generate())
   ```

4. **Run generation**:
   ```bash
   make codegen                 # Full pipeline including schema export
   cd apps/web && pnpm codegen  # Generate TypeScript from updated schema
   ```

## Current IR-Based Generation System

The code generation system uses IR-based patterns with key features:

1. **Intermediate Representation**: JSON files as single source of truth
2. **IR Builders**: Consolidate extraction logic in dedicated modules
3. **Template Job Nodes**: Direct rendering from IR data
4. **Dynamic Discovery**: Glob patterns find all files automatically
5. **External Code**: IR builders in `projects/codegen/code/` for reusability
6. **Batch Processing**: Parallel generation of multiple nodes
7. **Better Error Handling**: Graceful degradation in batch operations

Example pattern:
```yaml
- label: Generate Field Configs
  type: template_job
  props:
    template_path: projects/codegen/templates/frontend/field_config.jinja2
    output_path: "{{ output_dir }}/fields/{{ node_type_pascal }}Fields.ts"
    context:
      node_type: "{{ node_type }}"
      fields: "{{ fields }}"
      # ... other context
```

## Custom Template System

DiPeO uses Jinja2 templates with custom filters:

**Type Conversion Filters**:
- `ts_to_python` - Convert TypeScript types to Python
- `ts_to_graphql` - Convert TypeScript types to GraphQL
- `get_zod_type` - Get Zod validation type
- `get_graphql_type` - Get GraphQL type

**Naming Convention Filters**:
- `snake_case`, `camel_case`, `pascal_case` - Case conversions
- `pluralize` - Collection naming

**Key Generators**:
- `/projects/codegen/code/models/` - Python model generation
- `/projects/codegen/code/frontend/` - React/TypeScript generation
- All use external files for testability and reuse

## Key Files and Directories

### Source Files
- `/dipeo/models/src/` - TypeScript specifications (source of truth)
  - `/node-specs/` - Node type definitions
  - `/core/` - Core domain types
  - `/codegen/` - Code generation mappings

### Code Generation System
- `/projects/codegen/diagrams/` - DiPeO diagrams orchestrating generation
  - `generate_all.light.yaml` - Master orchestration
  - `generate_backend_simplified.light.yaml` - Backend from IR
  - `generate_frontend_simplified.light.yaml` - Frontend from IR
  - `generate_strawberry.light.yaml` - GraphQL from IR
- `/projects/codegen/code/` - IR builders and extractors
  - `backend_ir_builder.py` - Consolidates backend models/types
  - `frontend_ir_builder.py` - Extracts frontend components/schemas
  - `strawberry_ir_builder.py` - GraphQL operations & domain types
- `/projects/codegen/ir/` - Intermediate representation JSON files
  - `backend_ir.json` - Node specs, models, enums
  - `frontend_ir.json` - Components, schemas, fields
  - `strawberry_ir.json` - GraphQL operations, types, inputs
- `/projects/codegen/templates/` - Jinja2 templates consuming IR data
  - `/backend/` - Python model templates
  - `/frontend/` - TypeScript/React templates
  - `/strawberry/` - GraphQL/Strawberry templates

### Generated Files (DO NOT EDIT)
- `/dipeo/diagram_generated_staged/` - Staging directory for preview
- `/dipeo/diagram_generated/` - Active generated Python code
- `/apps/web/src/__generated__/` - Generated frontend code
- `/temp/` - Cached AST files (git-ignored)

### Configuration
- `/apps/web/codegen.yml` - GraphQL code generator config
- `Makefile` - Orchestrates the generation pipeline

## Architecture Notes

### v1.0 Refactoring Completed

The system has completed major architectural improvements:
- **Mixin-based Services**: Optional composition instead of monolithic inheritance
- **Unified EventBus**: Consolidated event protocols into single interface
- **Direct Protocol Implementation**: Eliminated unnecessary adapter layers
- **Enhanced Type Safety**: Improved Result types and JSON definitions
- **Snake_case Naming**: Python follows conventions with Pydantic aliases for compatibility
- **Generated Enums**: All enums now generated from TypeScript specifications

### Why Make Commands Over Master Diagrams

The codebase uses Make commands rather than a single master diagram because:
- **Better error handling**: Make stops on first error
- **Clear execution flow**: Each step is explicit
- **Easier debugging**: Can run individual steps or inspect IR
- **Standard tooling**: Developers know Make
- **IR Inspection**: Can examine intermediate JSON files

### Two-Stage GraphQL Generation

The system generates GraphQL in two stages:
1. **DiPeO generates queries** from domain knowledge
2. **GraphQL codegen generates TypeScript** from queries + schema

This provides:
- **Domain-driven queries**: Operations match your domain model
- **Type safety**: End-to-end from Python to TypeScript  
- **Flexibility**: Can customize queries without changing schema
- **Consistency**: All queries follow same patterns

### IR-Based Code Organization

All generation logic flows through IR builders:
- **IR Builders**: Centralized extraction logic in `*_ir_builder.py` files
- **Templates**: Consume IR data for consistent generation
- **Pattern**: `AST Parse → Build IR → Template → Output`
- Enables unit testing of extraction and generation logic
- Supports code reuse across diagrams
- IR files can be inspected for debugging in `projects/codegen/ir/`

## Best Practices

1. **Never edit generated files** - They will be overwritten
2. **Run `make codegen` after any spec changes** - Rebuilds IR and regenerates code
3. **Use `make diff-staged` to preview changes** - Review before applying
4. **Run `make apply` manually only when needed** - The full codegen includes it
5. **Use typed operations** - Leverage generated hooks in frontend
6. **Follow naming conventions**:
   - Queries: `Get{Entity}`, `List{Entities}`
   - Mutations: `Create{Entity}`, `Update{Entity}`, `Delete{Entity}`
   - Subscriptions: `{Entity}Updates`

## Troubleshooting

**Missing types after adding node**:
```bash
make codegen           # Regenerate everything with IR
make apply-test # Apply staged changes
make graphql-schema    # Update schema
make dev-all          # Restart servers
```

**IR debugging**:
```bash
# Inspect IR files to understand what's being generated
cat projects/codegen/ir/backend_ir.json | jq '.node_specs[0]'
cat projects/codegen/ir/frontend_ir.json | jq '.components[0]'
cat projects/codegen/ir/strawberry_ir.json | jq '.operations[0]'
```

**GraphQL query not found**:
1. Check query file was generated in `/apps/web/src/__generated__/queries/`
2. Ensure `pnpm codegen` was run in `/apps/web/`
3. Verify query name matches in component

**Type mismatch errors**:
- Schema and queries may be out of sync
- IR may be outdated
- Run full generation workflow:
  ```bash
  make codegen          # Rebuild IR and regenerate
  make apply-test
  make graphql-schema
  ```

## Conclusion

DiPeO's IR-based code generation system demonstrates the platform's maturity through its dog-fooding approach. By using DiPeO diagrams to orchestrate the generation of DiPeO's own code through intermediate representation, the system proves its robustness and capabilities. The IR architecture eliminates duplication, centralizes extraction logic, and provides a single source of truth for all generation targets. Combined with staging directories and parallel batch processing, this shows how visual programming can handle sophisticated meta-programming tasks while maintaining type safety from TypeScript specifications through IR to Python models and GraphQL operations.
