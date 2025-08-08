# Code Generation Guide

## Overview

DiPeO uses a diagram-driven, multi-stage code generation pipeline that "dog-foods" its own execution engine. All code generation is orchestrated through DiPeO diagrams, maintaining type safety from TypeScript node specifications to GraphQL queries and Python handlers.

## Generation Flow

```
1. Node Specifications (TypeScript in /dipeo/models/src/)
   ↓
2. Run generate_all diagram (dipeo run codegen/diagrams/generate_all)
   ├─→ Parse TypeScript → Cache AST (automatic discovery via glob)
   ├─→ Generate Domain Models → /dipeo/diagram_generated_staged/
   └─→ Generate Frontend Code → /apps/web/src/__generated__/
   ↓
3. Verify staged code in /dipeo/diagram_generated_staged/
   ↓
4. Apply Staged Changes (make apply-syntax-only)
   ↓
5. Export GraphQL Schema → /apps/server/schema.graphql
   ↓
6. Generate TypeScript Types (pnpm codegen)
```

**Key Features**:
- **Unified Generation**: Single `generate_all` diagram handles both models and frontend in parallel
- **Staging Directory**: Changes preview in `/dipeo/diagram_generated_staged/` before applying
- **Dynamic Discovery**: Automatically finds all TypeScript files using glob patterns
- **External Code**: All generation logic in `files/codegen/code/` for reusability
- **Syntax Validation**: Default validation ensures generated code is syntactically correct

### Stage 1: TypeScript Parsing & Caching

**Source**: All TypeScript files in `/dipeo/models/src/`  
**Cache**: `/temp/codegen/` and `/temp/core/` (AST JSON files)  
**Diagram**: `codegen/diagrams/shared/parse_typescript_batch.light.yaml`

The system automatically discovers and parses all TypeScript files, caching their AST for subsequent stages.

### Stage 2: Unified Code Generation

**Source**: Cached AST files + TypeScript specifications  
**Diagram**: `codegen/diagrams/generate_all.light.yaml`  
**Outputs**:
- Domain models → `/dipeo/diagram_generated_staged/`
- Frontend code → `/apps/web/src/__generated__/`

The `generate_all` diagram runs both model and frontend generation in parallel:

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

### Stage 3: Apply Staged Changes

**Action**: Manual copy from `/dipeo/diagram_generated_staged/` → `/dipeo/diagram_generated/`  
**Validation**: Syntax-only by default (Python compilation check)

Use `make apply-syntax-only` or `make apply` to move staged backend code to active directory. This ensures:
- Validated code before activation
- Ability to review changes before applying
- Rollback safety if generation has issues

### Stage 4: Export GraphQL Schema

**Command**: `make graphql-schema`  
**Output**: `/apps/server/schema.graphql`

Exports the complete GraphQL schema from the application layer, capturing all types and operations from the generated Strawberry types.

### Stage 5: GraphQL TypeScript Generation

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
# Step 1: Generate all code (models + frontend)
dipeo run codegen/diagrams/generate_all --light --debug --timeout=90

# Step 2: Verify staged changes
make diff-staged           # Compare staged vs active files

# Step 3: Apply staged backend code
make apply-syntax-only     # Apply with syntax validation only
# OR
make apply                 # Apply with full mypy type checking

# Step 4: Update GraphQL schema and types
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
make apply-syntax-only     # Apply with syntax validation only
make backup-generated      # Backup before applying changes
```

### Direct Diagram Execution (Advanced)

```bash
# Generate everything (models + frontend)
dipeo run codegen/diagrams/generate_all --light --debug

# Generate specific node (for debugging)
dipeo run codegen/diagrams/models/generate_backend_models_single --light \
  --input-data '{"node_name": "person_job"}'
```

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
   
   class MyNodeHandler(BaseNodeHandler[MyNodeData]):
       async def execute(self, data: MyNodeData, context: ExecutionContext):
           # Implementation
   ```

3. **Run code generation**:
   ```bash
   # Generate all code with the new node
   dipeo run codegen/diagrams/generate_all --light --debug
   
   # Apply staged changes
   make apply-syntax-only
   
   # Update GraphQL schema
   make graphql-schema
   ```

4. **The node is now available** with:
   - Full type safety across Python and TypeScript
   - Auto-generated UI components
   - GraphQL types and operations
   - Validation schemas

### Adding New GraphQL Queries/Mutations

1. **For existing entities**, modify the query generator:
   ```python
   # /files/codegen/code/frontend/generators/query_generator_dipeo.py
   # In generate_diagram_queries() or similar method
   
   queries.append("""query MyNewQuery($id: ID!) {
     diagram(id: $id) {
       # Add fields
     }
   }""")
   ```

2. **For new entities**, create a new query generator:
   ```python
   # /files/codegen/code/frontend/queries/my_entity_queries.py
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

### Adding New Mutations

1. **Add to schema** (`/apps/server/schema.graphql`):
   ```graphql
   type Mutation {
     myNewMutation(input: MyInput!): MyResult!
   }
   ```

2. **Add to query generator**:
   ```python
   queries.append("""mutation MyNewMutation($input: MyInput!) {
     myNewMutation(input: $input) {
       success
       data {
         id
       }
       error
     }
   }""")
   ```

3. **Implement resolver** in `/dipeo/application/graphql/`:
   ```python
   @strawberry.mutation
   async def my_new_mutation(self, input: MyInput) -> MyResult:
       # Implementation
   ```

## Key Files and Directories

### Source Files
- `/dipeo/models/src/` - TypeScript specifications (source of truth)
  - `/node-specs/` - Node type definitions
  - `/core/` - Core domain types
  - `/codegen/` - Code generation mappings

### Code Generation System
- `/files/codegen/diagrams/` - DiPeO diagrams orchestrating generation
  - `/models/` - Domain model generation diagrams
  - `/frontend/` - Frontend generation diagrams
  - `/shared/` - Shared parsing and utilities
- `/files/codegen/code/` - External Python code for diagrams
  - Organized to match diagram structure
  - All generation logic externalized for testing
- `/files/codegen/templates/` - Jinja2 templates
  - `/models/` - Python model templates
  - `/frontend/` - TypeScript/React templates

### Generated Files (DO NOT EDIT)
- `/dipeo/diagram_generated_staged/` - Staging directory for preview
- `/dipeo/diagram_generated/` - Active generated Python code
- `/apps/web/src/__generated__/` - Generated frontend code
- `/temp/` - Cached AST files (git-ignored)

### Configuration
- `/apps/web/codegen.yml` - GraphQL code generator config
- `Makefile` - Orchestrates the generation pipeline

## Architecture: Dog-fooding Approach

DiPeO's code generation is a prime example of "dog-fooding" - using DiPeO diagrams to generate DiPeO's own code:

1. **Visual Programming**: Each generation step is a diagram node
2. **Composability**: Sub-diagrams handle specific generation tasks
3. **Parallelization**: Batch processing for multiple files
4. **Error Handling**: Graceful degradation in batch operations
5. **Caching**: AST parsing cached to avoid redundant work

## Why The Staging Approach Matters

The staging directory (`diagram_generated_staged`) serves critical purposes:

1. **Preview Changes**: Review generated code before applying
2. **Atomic Updates**: All-or-nothing application of changes
3. **Syntax Validation**: Catch errors before they break the system
4. **Rollback Safety**: Easy to discard bad generations
5. **Frontend Dependency**: Frontend reads from applied (not staged) models

## Best Practices

1. **Never edit generated files** - They will be overwritten
2. **Run `make codegen` after any spec changes** - Handles the full pipeline automatically
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
dipeo run codegen/diagrams/generate_all --light --debug  # Regenerate everything
make apply-syntax-only                                   # Apply staged changes
make graphql-schema                                      # Update schema
make dev-all                                            # Restart servers
```

**GraphQL query not found**:
1. Check query file was generated in `/apps/web/src/__generated__/queries/`
2. Ensure `pnpm codegen` was run in `/apps/web/`
3. Verify query name matches in component

**Type mismatch errors**:
- Schema and queries may be out of sync
- Run full generation workflow:
  ```bash
  dipeo run codegen/diagrams/generate_all --light --debug
  make apply-syntax-only
  make graphql-schema
  ```

## V2 Generation Improvements

The current generation system uses "v2" diagrams with key improvements:

1. **Template Job Nodes**: Direct template rendering without intermediate steps
2. **Dynamic Discovery**: Glob patterns find all files automatically
3. **External Code**: All logic in `files/codegen/code/` for reusability
4. **Batch Processing**: Parallel generation of multiple nodes
5. **Better Error Handling**: Graceful degradation in batch operations

Example v2 pattern:
```yaml
- label: Generate Field Configs
  type: template_job
  props:
    template_path: files/codegen/templates/frontend/field_config_v2.jinja2
    output_path: "{{ output_dir }}/fields/{{ node_type_pascal }}Fields.ts"
    context:
      node_type: "{{ node_type }}"
      fields: "{{ fields }}"
      # ... other context
```

## Architecture Notes

### Why Make Commands Over Master Diagrams

The codebase uses Make commands rather than a single master diagram because:
- **Better error handling**: Make stops on first error
- **Clear execution flow**: Each step is explicit
- **Easier debugging**: Can run individual steps
- **Standard tooling**: Developers know Make

### Two-Stage GraphQL Generation

The system generates GraphQL in two stages:
1. **DiPeO generates queries** from domain knowledge
2. **GraphQL codegen generates TypeScript** from queries + schema

This provides:
- **Domain-driven queries**: Operations match your domain model
- **Type safety**: End-to-end from Python to TypeScript  
- **Flexibility**: Can customize queries without changing schema
- **Consistency**: All queries follow same patterns

### External Code Organization

All generation logic lives in external Python files:
- Matches diagram structure for discoverability
- Enables unit testing of generation logic
- Supports code reuse across diagrams
- Example: `parse_typescript_single.light.yaml` uses functions from `files/codegen/code/shared/typescript_spec_parser.py`