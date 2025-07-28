# Phase 0 Summary: GraphQL Migration Architecture Lock

## Completed Tasks

### 1. Analyzed Current Schema Structure
- Current schema uses generic `CreateNodeInput` with `type: NodeType` enum and `data: JSONScalar`
- All node data is stored as untyped JSON, losing type safety
- Complex triple re-export pattern in `types_new.py`

### 2. Documented Architectural Decisions
Created `/docs/graphql-architecture-decisions.md` with:
- **Interface-based design**: Node interface with concrete types
- **Per-node mutations**: Type-safe create operations
- **Generation pipeline**: TS → JSON Schema → Pydantic → Strawberry
- **Type mapping rules**: Drop Literals, use __typename
- **Compatibility strategy**: Additive-only with deprecation

### 3. Created /v2/graphql Endpoint
- New endpoint accessible at `http://localhost:8000/v2/graphql`
- Separate from current schema to allow parallel development
- GraphQL playground available for testing

### 4. Prototyped Interface Design
Implemented proof of concept with:
- `interface Node` with id and position
- Three concrete types: PersonNode, CodeNode, StartNode
- Flattened fields (no nested data object)
- Per-node mutations with typed inputs

### 5. Verified Schema Export
Generated schema shows clean structure:
```graphql
interface Node {
  id: NodeID!
  position: Point!
}

type PersonNode implements Node {
  id: NodeID!
  position: Point!
  person_id: PersonID!
  model: String!
  prompt: String!
  temperature: Float!
  # ... flattened fields
}

type Mutation {
  create_person_node(diagram_id: DiagramID!, input: CreatePersonNodeInput!): PersonNodeResult!
  create_code_node(diagram_id: DiagramID!, input: CreateCodeNodeInput!): CodeNodeResult!
  # ... per-node mutations
}
```

## Key Architecture Locked

1. **NO** giant data unions or generic node types
2. **NO** Literal types in GraphQL (use __typename)
3. **YES** to interfaces for polymorphism
4. **YES** to per-node mutations
5. **YES** to flattened, typed fields

## Next Steps (Phase 1)

1. Set up Pydantic validation pipeline
2. Implement actual resolvers for the prototype nodes
3. Add more node types following the pattern
4. Create JSON Schema generation from TypeScript specs
5. Wire up runtime validation

## Files Created
- `/docs/graphql-architecture-decisions.md`
- `/apps/server/src/dipeo_server/api/graphql/v2/schema.py`
- `/apps/server/src/dipeo_server/api/graphql/v2/types.py`
- `/apps/server/src/dipeo_server/api/graphql/v2/__init__.py`
- `/apps/server/schema_v2.graphql` (exported)

## Testing
Server starts successfully with both endpoints:
- Current: `http://localhost:8000/graphql`
- V2: `http://localhost:8000/v2/graphql`