# DiPeO Models Package

TypeScript library serving as the single source of truth for all domain models.

## Architecture

`TypeScript Sources → AST Parser → Code Generators → Python/GraphQL/Frontend Code`

## Structure

```
src/
├── nodes/              # Node specifications (first-class citizens)
│   ├── *.spec.ts      # 14 node specification files
│   └── index.ts       # Node spec exports
├── node-specification.ts  # Node spec types & interfaces
├── node-categories.ts     # Node categorization
├── node-registry.ts       # Central node registry
├── core/               # Domain models, enums
├── frontend/           # Query specifications
├── codegen/            # AST types, mappings
└── utilities/          # Type conversions
```

## Key Components

### Node Specifications (`nodes/`)
- **Primary source of truth** for all node types
- 14 node specifications: start, api-job, code-job, condition, db, endpoint, hook, integrated-api, json-schema-validator, person-job, sub-diagram, template-job, typescript-ast, user-response
- Each spec defines metadata, fields, UI config, validation rules, and behavior

### Core Models (`core/`)
- **Diagram**: DomainNode, DomainArrow, DomainHandle, DomainDiagram
- **Execution**: ExecutionState, ExecutionContext
- **Enums**: NodeType, ExecutionStatus, LLMService, MemoryView, etc.

### Frontend (`frontend/`)
- GraphQL query specifications
- CRUD, relationships, subscriptions

### Code Generation (`codegen/`)
- AST types, mappings, node-interface map

## Code Generation Pipeline

1. **Parse**: TypeScript AST extraction
2. **Cache**: Results to `.temp/ast_cache/`
3. **Generate** (parallel):
   - Python models → `dipeo/diagram_generated/domain_models.py`
   - GraphQL schema → `dipeo/diagram_generated/domain-schema.graphql`
   - Frontend configs → `apps/web/src/__generated__/`

## Type System

```typescript
// Branded types for compile-time safety
export type NodeID = string & { readonly __brand: 'NodeID' };

// Union types for flexibility
export type DataType = 'any' | 'string' | 'number' | 'boolean' | 'object' | 'array';

// Nested configurations
export interface MemorySettings {
  view: MemoryView;
  max_messages?: number;
}
```

## Integration

- **Frontend**: Direct TypeScript import via `@dipeo/models`
- **Backend**: Generated Pydantic models
- **GraphQL**: Generated schema
- **Validation**: Generated Zod schemas

## Workflow

### Adding a New Node Type
1. Create spec file in `src/nodes/[node-name].spec.ts`
2. Export from `src/nodes/index.ts`
3. Add to registry in `src/node-registry.ts`
4. Build: `cd dipeo/models && pnpm build`
5. Generate: `make codegen`
6. Changes propagate to Python models, GraphQL schema, and frontend

### Modifying Existing Nodes
1. Edit spec file in `src/nodes/`
2. Build: `cd dipeo/models && pnpm build`
3. Generate: `make codegen`
4. Changes propagate to all consumers

## Benefits

- **Single Source of Truth**: Node specifications drive all code generation
- **First-Class Node Specs**: Clear, top-level organization emphasizes nodes as core concept
- **Type Safety**: Across TypeScript, Python, and GraphQL
- **Automated Sync**: Changes propagate automatically to all consumers
- **Zero Boilerplate**: Code generation handles duplication
- **Clear Architecture**: Flat structure makes node specs immediately discoverable
