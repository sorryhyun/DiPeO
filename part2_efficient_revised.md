# Part 2: Efficient GraphQL Schema Migration (Revised)

## Architecture Understanding

After deeper investigation, we discovered the correct architecture:

1. **Node Data Models** (`/dipeo/diagram_generated/models/`): 
   - Pydantic models containing only node-specific fields (e.g., `ApiJobNodeData`)
   - These are perfect for GraphQL type generation
   - No id/position fields - those are handled at the diagram level

2. **Node Classes** (`/dipeo/diagram_generated/nodes/`):
   - Frozen dataclasses with complete node structure
   - Cannot be used with `@strawberry.experimental.pydantic.type()`
   - Used internally by the execution engine

3. **GraphQL Architecture**:
   - Generic `DomainNode` with `data: Dict[str, Any]` for flexibility
   - Node-specific types should enhance, not replace this system
   - Focus on type-safe data fields, not complete node replacement

## Revised Strategy: Type-Safe Node Data

### Goal
Generate Strawberry GraphQL types that provide type safety for node-specific data fields while working with the existing generic node system.

### Implementation Plan

#### Phase 1: Generate Data Types ✅
Generate Strawberry types from `*NodeData` Pydantic models:

```python
# Example generated type
@strawberry.experimental.pydantic.type(ApiJobNodeData, all_fields=True)
class ApiJobNodeDataType:
    """API Job node data fields"""
    pass
```

These types represent just the data portion of nodes, providing type safety for mutations and queries.

#### Phase 2: Generate Type-Safe Mutations 📝

Create mutations with proper input types for each node:

```graphql
mutation CreateApiJobNode($input: CreateApiJobNodeInput!) {
  createApiJobNode(input: $input) {
    id
    data {
      url
      method
      headers
    }
  }
}
```

The mutations should:
1. Accept typed inputs for node-specific fields
2. Work with the existing diagram service
3. Return the created/updated node with typed data

#### Phase 3: Enhance Existing Types 📝

Instead of replacing the node system, enhance it:

```python
@strawberry.type
class DomainNodeType:
    id: strawberry.auto
    type: strawberry.auto
    position: strawberry.auto
    
    @strawberry.field
    def data(self) -> NodeDataUnion:
        """Returns typed data based on node type"""
        # Resolve to correct data type based on node.type
        return resolve_node_data(self)
```

## Benefits of This Approach

1. **Incremental Migration**: Works alongside existing system
2. **Type Safety**: Provides typing for node-specific fields
3. **Backward Compatible**: Doesn't break existing GraphQL API
4. **Code Generation**: Automated from TypeScript specs
5. **Flexibility**: Generic system still available when needed

## Implementation Status

### Completed ✅
- Strawberry type generator created
- Templates for types and mutations
- Integration with codegen pipeline
- Basic type generation working

### Next Steps 📝
1. Fix templates to generate proper data types (not full node types)
2. Generate field-specific input types from node specs
3. Create resolver functions for typed data access
4. Test with real queries and mutations
5. Document usage patterns

## Key Learnings

1. **Don't over-engineer**: The existing generic system works well
2. **Enhance, don't replace**: Add type safety where it helps
3. **Respect the architecture**: Frontend and backend have different needs
4. **Data models are key**: The `*NodeData` models are perfect for GraphQL

## Migration Path

### Phase 1: Data Types (Current)
- Generate types for node data
- Use in new mutations
- Keep existing queries working

### Phase 2: Enhanced Queries
- Add typed data resolvers
- Provide both generic and typed access
- Gradual frontend adoption

### Phase 3: Full Type Safety
- Complete input type generation
- Validation at GraphQL layer
- Frontend fully typed

This revised approach respects the existing architecture while adding valuable type safety where it matters most - in the node-specific data fields.