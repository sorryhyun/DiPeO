# DiPeO Code Generation & GraphQL Schema Architecture

## Overview

DiPeO uses a sophisticated code generation pipeline with TypeScript domain models as the single source of truth. The system generates Python models, GraphQL schemas, and TypeScript types to ensure type consistency across the entire stack.

## Architecture Flow

```
┌─────────────────────────┐
│  TypeScript Domain      │  ← Single Source of Truth
│  (domain-models/src/)   │    - diagram.ts, execution.ts, conversation.ts
└───────────┬─────────────┘
            │
            ▼ npm run build
┌─────────────────────────┐
│  Schema Extraction      │  ← ts-morph analyzes TypeScript AST
│  (generate-schema.ts)   │    → outputs schemas.json
└───────────┬─────────────┘
            │
      ┌─────┴─────┬─────────────┬──────────────┐
      ▼           ▼             ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Python   │ │ GraphQL  │ │   CLI    │ │TypeScript│
│ Models   │ │  Schema  │ │  Models  │ │  Types   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
     │            │             │
     ▼            ▼             ▼
  Backend     Server API    CLI Tool    (direct import)
```

## Generation Pipeline

### 1. TypeScript → JSON Schema
**Script**: `generate-schema.ts`
- Uses ts-morph to parse TypeScript AST
- Extracts interfaces, enums, and their properties
- Outputs `__generated__/schemas.json`

### 2. JSON Schema → Python Models
**Script**: `generate-python.ts`
- Reads schemas.json
- Generates Pydantic models with:
  - Proper type mappings (TS → Python)
  - Snake_case field names with aliases
  - Optional fields handling
  - Branded types as NewType

**Output**: `packages/python/dipeo_domain/src/dipeo_domain/models.py`

### 3. TypeScript → GraphQL Schema
**Script**: `generate-graphql.ts`
- Direct TypeScript to GraphQL SDL conversion
- Maps TypeScript types to GraphQL types
- Handles enums, unions, and custom scalars

**Output**: `packages/domain-models/schema.graphql`

### 4. Server → GraphQL Schema Export
The FastAPI server uses Strawberry GraphQL to:
- Define queries, mutations, and subscriptions
- Export complete schema including operations
- Use Pydantic models for type safety

**Output**: `apps/server/schema.graphql`

### 5. GraphQL Schema → TypeScript Types
**Tool**: GraphQL Code Generator (`codegen.yml`)
- Reads server's GraphQL schema
- Generates TypeScript types and React hooks
- Maps custom scalars to branded types from domain-models

**Output**: `apps/web/src/__generated__/graphql.tsx`

## Key Components

### Branded Types
TypeScript branded types ensure type safety:
```typescript
export type NodeID = string & { readonly __brand: 'NodeID' };
```

Mapped in Python as:
```python
NodeID = NewType('NodeID', str)
```

### Type Mappings

| TypeScript | Python | GraphQL |
|------------|--------|---------|
| string | str | String |
| number | float/int | Float |
| boolean | bool | Boolean |
| T[] | List[T] | [T] |
| Record<K,V> | Dict[K,V] | JSON |
| enum | Enum | enum |

### Field Name Conversion
- TypeScript: `camelCase`
- Python: `snake_case` (with Pydantic aliases)
- GraphQL: `camelCase`

## Build Process

1. **Initial Setup**: `./build-all.sh`
   - Builds domain models
   - Installs Python packages
   - Generates GraphQL schema
   - Runs frontend codegen

2. **Development Workflow**:
   ```bash
   # After changing domain models:
   cd packages/domain-models
   pnpm build  # Regenerates all derived code
   
   # After changing server GraphQL:
   cd apps/server
   python -m dipeo_server.api.graphql.schema > schema.graphql
   
   # Update frontend types:
   cd apps/web
   pnpm codegen
   ```

## GraphQL Architecture

### Schema Organization
- **Types**: Auto-generated from domain models
- **Queries**: Defined in `queries.py`
- **Mutations**: Modular (per domain) in `mutations/`
- **Subscriptions**: Real-time updates in `subscriptions.py`

### Strawberry Integration
```python
@strawberry.experimental.pydantic.type(DomainNode, all_fields=True)
class DomainNodeType:
    # Automatic conversion from Pydantic models
    pass
```

### Custom Scalars
Defined in both schema and codegen config:
- NodeID, DiagramID, ExecutionID, etc.
- DateTime, JSONScalar

## Benefits

1. **Type Safety**: End-to-end type checking from database to UI
2. **Single Source of Truth**: All types derive from TypeScript models
3. **Consistency**: Field names, enums, and types stay synchronized
4. **Developer Experience**: Auto-completion and type checking everywhere
5. **Maintainability**: Change types in one place, regenerate everywhere

## Common Tasks

### Adding a New Field
1. Add to TypeScript interface in `domain-models/src/`
2. Run `pnpm build` in domain-models
3. Restart server to load new Python models
4. Run `pnpm codegen` in web app

### Adding a New Type
1. Create interface/enum in domain-models
2. Follow same regeneration process
3. Add GraphQL operations as needed
4. Update codegen if using new scalars

### Debugging Generation
- Check `__generated__/schemas.json` for extraction issues
- Python models have clear imports at top
- GraphQL schema is human-readable
- Use `--verbose` flags in generation scripts