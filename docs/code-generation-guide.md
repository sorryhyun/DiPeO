# Code Generation Guide

## Overview

DiPeO uses a multi-stage code generation pipeline to maintain type safety from TypeScript node specifications to GraphQL queries and Python handlers.

## Generation Flow

```
1. Node Specifications (TypeScript)
   ↓
2. Generate Domain Models → /dipeo/diagram_generated_staged/
   ↓
3. Generate Backend Code
   ↓
4. Apply Staged Changes (make apply)
   ↓
5. Generate Frontend Code (depends on applied models)
   ↓
6. Export GraphQL Schema (make graphql-schema)
```

**Important**: The code generation process uses a staging directory (`/dipeo/diagram_generated_staged/`) to preview domain model changes before applying them. This ensures frontend generation sees the latest domain models.

### Stage 1: Node Specifications → Python Models

**Source**: `/dipeo/models/src/node-specs/*.spec.ts`  
**Staged Output**: `/dipeo/diagram_generated_staged/`  
**Final Output**: `/dipeo/diagram_generated/`  
**Commands**: 
```bash
make codegen  # Runs full pipeline including apply
# Or manually:
dipeo run codegen/diagrams/models/generate_all_models --light --debug
make apply    # Apply staged changes
```

Generates:
- Pydantic models (`/models/`)
- JSON schemas (`/schemas/`)
- Validation models (`/validation/`)
- Node configurations (`/nodes/`)

### Stage 2: Backend Code Generation

**Source**: TypeScript node specifications  
**Output**: Python node handlers and configurations  
**Command**: Part of `make codegen` pipeline

Generates backend-specific files for each node type.

### Stage 3: Apply Staged Changes

**Command**: `make apply`  
**Action**: Copies `/dipeo/diagram_generated_staged/` → `/dipeo/diagram_generated/`

This critical step ensures that:
- Frontend generation sees the latest domain models
- All components use consistent type definitions
- Changes can be reviewed before applying

### Stage 4: Frontend Code Generation

**Source**: Applied domain models + TypeScript specs  
**Output**: 
- `/apps/web/src/__generated__/queries/*.graphql` - GraphQL queries
- Frontend node configurations and components

Generates:
- `diagrams.graphql` - Diagram CRUD operations
- `persons.graphql` - Person management
- `executions.graphql` - Execution monitoring
- Node-specific UI components and configs

### Stage 5: Export GraphQL Schema

**Command**: `make graphql-schema`  
**Output**: `/apps/server/schema.graphql`

Exports the complete GraphQL schema from the running server, ensuring:
- Schema reflects all current types and operations
- Frontend codegen has up-to-date schema
- Documentation stays synchronized

### Stage 6: GraphQL TypeScript Generation

**Source**: `/apps/web/src/__generated__/queries/*.graphql` + `/apps/server/schema.graphql`  
**Output**: `/apps/web/src/__generated__/graphql.tsx`  
**Command**: `pnpm codegen` (in apps/web)

Generates:
- TypeScript types for all GraphQL operations
- React hooks (useQuery, useMutation, useSubscription)
- Apollo Client integration code

## Adding New Features

### Adding a New Node Type

1. **Create node specification**:
   ```typescript
   // /dipeo/models/src/node-specs/my-node.spec.ts
   export const myNodeSpec: NodeSpecification = {
     nodeType: NodeType.MyNode,
     category: 'processing',
     fields: [
       {
         name: 'myField',
         type: 'string',
         required: true,
         description: 'Description of the field'
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
   make codegen
   ```

4. **The node is now available** in the diagram editor with full type safety.

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

## Key Files

### Code Generation
- `/dipeo/models/src/node-specs/` - Node specifications (source of truth)
- `/files/codegen/code/frontend/generators/` - Query generators
- `/files/codegen/diagrams/` - Codegen orchestration diagrams

### Generated Files (DO NOT EDIT)
- `/dipeo/diagram_generated/` - Python models and schemas
- `/apps/web/src/__generated__/queries/` - GraphQL query definitions
- `/apps/web/src/__generated__/graphql.tsx` - TypeScript types and hooks

### Configuration
- `/apps/web/codegen.yml` - GraphQL code generator config
- `/dipeo/models/tsconfig.json` - TypeScript to JSON Schema config

## Why This Order Matters

The staged approach with `make apply` is crucial because:
1. **Domain models must be generated first** - They define the core types
2. **Backend generation can proceed independently** after domain models
3. **Apply must happen before frontend** - Frontend queries depend on the actual domain model files
4. **Frontend generation reads from applied models** - Not from staged directory
5. **GraphQL schema export must happen after all generation** - Captures all new types and operations
6. **Frontend TypeScript generation depends on exported schema** - Ensures type consistency

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
make codegen  # Regenerate everything
make dev-all  # Restart servers
```

**GraphQL query not found**:
1. Check query file was generated in `/apps/web/src/__generated__/queries/`
2. Ensure `pnpm codegen` was run in `/apps/web/`
3. Verify query name matches in component

**Type mismatch errors**:
- Schema and queries may be out of sync
- Run `make codegen` then `cd apps/web && pnpm codegen`

## Architecture Notes

The two-stage GraphQL generation (Python generates queries, then GraphQL codegen generates TypeScript) provides:
- **Domain-driven queries**: Operations match your domain model
- **Type safety**: End-to-end from Python to TypeScript  
- **Flexibility**: Can customize queries without changing schema
- **Consistency**: All queries follow same patterns

While the directory structure (`__generated__/queries/`) may seem confusing, these query files are source files for the GraphQL code generator, not its output. Only `graphql.tsx` is truly generated.