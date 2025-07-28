# GraphQL Architecture Decisions

## Overview
This document records the architectural decisions for the GraphQL schema migration, following expert advice on type safety and clean GraphQL design.

## Core Decisions

### 1. Schema Design: Interface-Based with Concrete Node Types

**Decision**: Use GraphQL interfaces for shared fields and concrete object types for each node type.

**Rationale**:
- Interfaces scale better than unions for 50+ node types
- Enables polymorphic queries with clean TypeScript discriminated unions
- Avoids the "giant data union" anti-pattern

**Implementation**:
```graphql
interface Node {
  id: ID!
  position: Point!
}

type PersonNode implements Node {
  id: ID!
  position: Point!
  model: String!
  prompt: String!
  temperature: Float!
}

type CodeNode implements Node {
  id: ID!
  position: Point!
  language: String!
  code: String!
}
```

### 2. Write API: Per-Node Mutations

**Decision**: Create specific mutations for each node type instead of generic create with JSON.

**Rationale**:
- Maximum type safety in TypeScript
- Better GraphQL introspection and documentation
- Compile-time validation on client
- GraphQL has no input unions, so this is the idiomatic approach

**Implementation**:
```graphql
type Mutation {
  createPersonNode(input: CreatePersonNodeInput!): PersonNode!
  createCodeNode(input: CreateCodeNodeInput!): CodeNode!
  # ... one per node type
}

input CreatePersonNodeInput {
  position: PointInput!
  model: String!
  prompt: String!
  temperature: Float
}
```

### 3. Generation Pipeline

**Decision**: TypeScript → JSON Schema → Pydantic → Strawberry with manual overrides

**Rationale**:
- Keeps GraphQL schema clean and idiomatic
- TypeScript and Python share validation truth via JSON Schema
- Avoids importing TypeScript-specific constructs into GraphQL
- Manual overrides handle edge cases without compromising the system

**Pipeline**:
1. Generate JSON Schema from TypeScript node specs
2. Generate Pydantic models from JSON Schema for runtime validation
3. Hand-design GraphQL schema (not auto-generated)
4. Use Pydantic models for input validation in resolvers

### 4. Type Mapping Rules

| TypeScript Pattern | GraphQL Output | GraphQL Input | Notes |
|-------------------|----------------|---------------|-------|
| `Literal["person"]` | Omit (use `__typename`) | `NodeType` enum | GraphQL has no literal types |
| Discriminated unions | Interface + concrete types | Separate input types | Best practice for polymorphism |
| Known object shapes | GraphQL object types | GraphQL input types | Preserve structure |
| Dynamic JSON | `JSON` scalar | `JSON` scalar + validator | Only for truly dynamic data |
| String enums | GraphQL enum | GraphQL enum | Direct mapping |

### 5. Compatibility Strategy

**Decision**: Additive-only changes with deprecation

**Implementation**:
- New schema at `/v2/graphql` endpoint during migration
- Use `@deprecated` directive for fields being removed
- Keep deprecated fields read-only for one release cycle
- Never break existing queries

**Example**:
```graphql
type DomainNode {
  id: ID!
  type: NodeType! @deprecated(reason: "Use __typename instead")
  data: JSON! @deprecated(reason: "Use typed fields on concrete node types")
}
```

## Migration Phases

### Phase 0 (Current): Lock Architecture
- Document these decisions ✓
- Create `/v2/graphql` endpoint
- Prototype with 2-3 node types

### Phase 1: Schema Baseline
- Implement Node interface
- Create concrete types for representative nodes
- Set up Pydantic validation
- Implement per-node mutations

### Phase 2: Generation Infrastructure
- Build TS → JSON Schema → Pydantic pipeline
- Add manual override system
- Convert 50% of nodes

### Phase 3: Performance
- Add DataLoader
- Implement caching
- Add monitoring

### Phase 4: Complete Migration
- Convert remaining nodes
- Deprecate old schema
- Switch clients to v2

## Non-Goals

These patterns are explicitly avoided:

1. **Auto-generating GraphQL from TypeScript** - Imports TS limitations
2. **Single node type with optional fields** - Loses type safety
3. **Giant `data` union** - Poor scaling and ergonomics
4. **JSON for known structures** - Loses client type safety
5. **Generic mutations with type + JSON** - Poor TypeScript support

## Success Criteria

- Zero JSONScalar usage for structured data
- All inputs validated with Pydantic
- Client receives discriminated unions via `__typename`
- No manual GraphQL type editing required
- Breaking changes caught by CI

## Next Steps

1. Create `/v2/graphql` endpoint
2. Implement Node interface
3. Create PersonNode and CodeNode as proof of concept
4. Set up Pydantic validation pipeline