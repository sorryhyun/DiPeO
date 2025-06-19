# DiPeO GraphQL Type System

## Core Principle
All diagram formats use GraphQL as the canonical representation. Frontend and backend convert to/from GraphQL for their specific needs.

## Conversions

### Frontend (TypeScript)
```typescript
// GraphQL → xyflow react (for rendering)
interface Converter {
  toReact(diagram: DiagramQL): ReactDiagram;
  toGraphQL(react: ReactFlowDiagram): DiagramQL;
  toStorage(diagram: DiagramQL): CompressedDiagram;
}
```

### Backend (Python)
```python
# GraphQL → Execution Graph (for running)
class ExecutionConverter:
    def to_networkx(self, diagram: dict) -> nx.DiGraph
    def resolve_handles(self, diagram: dict) -> Dict[str, Handle]
    def to_graphql(self, graph: nx.DiGraph) -> dict
```

## Operations

```graphql
type Query {
  diagram(id: ID!): DomainDiagram
  validateDiagram(input: DomainDiagramInput!): Diagram!
}

type Mutation {
  createDiagram(input: DomainDiagramInput!): DomainDiagram!
  updateDiagram(id: ID!, input: DomainDiagramInput!): DomainDiagram!
  executeDiagram(id: ID!): ExecutionStatus!
}

type Subscription {
  diagramExecution(id: ID!): ExecutionStatus!
}
```

## Key Design Decisions

1. **NodeID/ArrowID as scalars**: Type-safe identifiers
2. **Interface for Node types**: Extensible node system
3. **Handles as first-class entities**: Explicit connection points
4. **Separate Person from Node**: Clear LLM instance management
