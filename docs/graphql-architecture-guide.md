# GraphQL Architecture Guide

## Overview

DiPeO's GraphQL architecture follows clean architecture principles, with GraphQL schema definitions residing in the application layer (`@dipeo/application/graphql/`) while the server remains a thin HTTP adapter. This guide documents the complete type-safety pipeline from domain models to frontend queries.

## Architecture Principles

### 1. Clean Architecture Separation
```
┌─────────────────────┐
│   Domain Models     │  TypeScript source of truth
│  (@dipeo/models)    │  
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Application Layer   │  Business logic + GraphQL schema
│ (@dipeo/application │  with dependency injection
│     /graphql)       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Server Layer      │  Thin HTTP adapter only
│ (apps/server)       │  Injects service registry
└─────────────────────┘
```

### 2. Type Safety Pipeline
```
TypeScript → JSON Schema → Pydantic → Strawberry → GraphQL
    ↓             ↓            ↓          ↓           ↓
models/src/   schemas/    validation/  graphql/    API
node-specs/   nodes/      nodes/       types/
```

### 3. Single Source of Truth
- **Domain Models**: TypeScript interfaces define all data structures
- **No Manual Types**: Everything is generated or derived from domain models
- **Bidirectional Safety**: Types flow from backend models to frontend queries

## Current Implementation

### Application Layer GraphQL (`@dipeo/application/graphql/`)

```
dipeo/application/graphql/
├── schema_factory.py      # Creates schema with dependency injection
├── resolvers/             # Business logic using UnifiedServiceRegistry
│   ├── diagram.py
│   ├── execution.py
│   └── person.py
├── schema/
│   ├── queries.py         # Query definitions
│   ├── mutation_factory.py # Mutation definitions
│   └── subscriptions.py   # Real-time subscriptions
└── types/
    ├── inputs.py          # GraphQL input types
    └── results.py         # GraphQL result types
```

### Key Features

1. **Dependency Injection**
   ```python
   # Schema accepts service registry
   schema = create_schema(registry: UnifiedServiceRegistry)
   ```

2. **Service-Based Resolvers**
   ```python
   class DiagramResolver:
       def __init__(self, registry: UnifiedServiceRegistry):
           self.registry = registry
       
       async def get_diagram(self, id: DiagramID):
           service = self.registry.require(INTEGRATED_DIAGRAM_SERVICE)
           return await service.get_diagram(id)
   ```

3. **Decoupled Server**
   ```python
   # Server just injects dependencies
   registry = container.service_registry
   schema = create_schema(registry)
   app.include_router(GraphQLRouter(schema))
   ```

## Type Generation Workflow

### 1. Define Node Specification
```typescript
// dipeo/models/src/node-specs/person-job.spec.ts
export const personJobSpec: NodeSpecification = {
  nodeType: NodeType.PersonJob,
  fields: [
    {
      name: "personId",
      type: "string",
      required: true,
      description: "ID of the person to use"
    }
  ]
}
```

### 2. Generate Artifacts
```bash
# Runs the complete generation pipeline
make codegen

# This generates:
# - Python models in dipeo/diagram_generated/
# - JSON schemas in dipeo/diagram_generated/schemas/
# - Validation models in dipeo/diagram_generated/validation/
```

### 3. Create GraphQL Types
```python
# Currently in dipeo/application/graphql/types/
# Will migrate to Strawberry experimental.pydantic

from dipeo.diagram_generated.domain_models import DomainDiagram

# Convert Pydantic to Strawberry (current gap)
DomainDiagramType = strawberry.experimental.pydantic.type(
    DomainDiagram,
    all_fields=True
)
```

## v2 Interface-Based Schema (In Progress)

Following GraphQL best practices for polymorphic types:

### Node Interface Pattern
```graphql
interface Node {
  id: ID!
  position: Point!
}

type PersonJobNode implements Node {
  id: ID!
  position: Point!
  personId: PersonID!
  defaultPrompt: String!
  memorySettings: MemorySettings
}
```

### Per-Node Mutations
```graphql
type Mutation {
  createPersonJobNode(input: CreatePersonJobNodeInput!): PersonJobNode!
  updatePersonJobNode(id: ID!, input: UpdatePersonJobNodeInput!): PersonJobNode!
  
  # One mutation per node type for maximum type safety
}
```

### Query with Interfaces
```graphql
query GetDiagram($id: ID!) {
  diagram(id: $id) {
    nodes {
      __typename  # For discrimination
      id
      position
      ... on PersonJobNode {
        personId
        defaultPrompt
      }
      ... on CodeJobNode {
        language
        code
      }
    }
  }
}
```

## Frontend Integration

### Query Generation Pipeline (Planned)
```
Domain Models → Query Templates → Generated Queries → TypeScript Types
      ↓               ↓                  ↓                    ↓
  node-specs/    query patterns    .graphql files      Apollo codegen
```

### Benefits
- Queries always match domain structure
- Automatic CRUD operations per entity
- Type-safe discriminated unions in TypeScript
- Reduced bundle size with interface field selection

## Adding New Features

### 1. Add a New Node Type

**Step 1**: Create TypeScript specification
```typescript
// dipeo/models/src/node-specs/my-node.spec.ts
export const myNodeSpec: NodeSpecification = {
  nodeType: NodeType.MyNode,
  category: "utility",
  fields: [...]
}
```

**Step 2**: Run generation
```bash
make codegen
```

**Step 3**: Add GraphQL type (temporary until auto-conversion)
```python
# In dipeo/application/graphql/types/nodes.py
@strawberry.type
class MyNode:
    # Match fields from generated model
```

**Step 4**: Add mutation
```python
# In dipeo/application/graphql/schema/mutations/node.py
@strawberry.mutation
async def create_my_node(self, input: CreateMyNodeInput) -> MyNode:
    # Implementation
```

### 2. Add a New Service

**Step 1**: Define port interface
```python
# dipeo/core/ports/my_service.py
class MyServicePort(Protocol):
    async def do_something(self) -> Result: ...
```

**Step 2**: Implement adapter
```python
# dipeo/infra/my_service/adapter.py
class MyServiceAdapter(MyServicePort):
    async def do_something(self) -> Result:
        # Implementation
```

**Step 3**: Register in container
```python
# In application container setup
registry.register(MY_SERVICE, MyServiceAdapter())
```

**Step 4**: Use in resolver
```python
service = self.registry.require(MY_SERVICE)
result = await service.do_something()
```

## Migration Status

### ✅ Completed
- GraphQL schema moved to application layer
- Dependency injection pattern implemented
- Service-based resolvers created
- Basic query/mutation structure

### 🚧 In Progress
- Pydantic to Strawberry type conversion
- v2 interface-based schema implementation
- Frontend query generation

### 📋 Planned
- Complete v2 schema with all node types
- Deprecate v1 schema endpoints
- Optimize query performance
- Generate documentation from schema

## Best Practices

1. **Never manually write GraphQL types** - Generate from domain models
2. **Use dependency injection** - All services via UnifiedServiceRegistry
3. **Keep resolvers thin** - Business logic in application services
4. **Validate with Pydantic** - Before any mutations
5. **Use interfaces** - For polymorphic types (nodes)
6. **Generate queries** - From domain model structure

## Troubleshooting

### Common Issues

**Pydantic to Strawberry conversion errors**
```python
# Use strawberry.experimental.pydantic
DomainType = strawberry.experimental.pydantic.type(
    PydanticModel,
    all_fields=True
)
```

**Missing service in registry**
```python
# Check service is registered
if not registry.has(SERVICE_KEY):
    registry.register(SERVICE_KEY, ServiceImpl())
```

**Type not found in schema**
```bash
# Ensure codegen was run
make codegen
# Check generated files exist
ls dipeo/diagram_generated/
```

## Future Architecture

### Domain-Driven Query Generation
- Automatic CRUD query generation per entity
- Relationship traversal patterns
- Optimized field selection

### Performance Optimizations
- DataLoader for N+1 prevention
- Query complexity analysis
- Automatic persisted queries

### Developer Experience
- Hot reload schema changes
- GraphQL playground with auth
- Automatic API documentation

## Summary

DiPeO's GraphQL architecture demonstrates clean separation of concerns with the schema residing in the application layer, dependency injection throughout, and a robust type-safety pipeline from TypeScript domain models to GraphQL API. The ongoing v2 interface-based schema will complete the vision of a fully type-safe, domain-driven API.