# Simplified Feature Addition Workflow

With the new code generation setup, adding new features to DiPeO is now much simpler. You only need to modify TypeScript models, and all other types are automatically generated.

## Example: Adding a "Comment" Feature to Nodes

### Before (Manual Process)
Previously, you had to manually update 3-4 files:
1. TypeScript models in `@dipeo/models/`
2. Python GraphQL types in `@apps/server/src/dipeo_server/api/graphql/types.py`
3. Frontend type mappings in `@apps/web/src/core/`
4. GraphQL schema definitions

### After (Automated Process)
Now you only need to:

#### 1. Add the TypeScript Model

```typescript
// dipeo/models/src/diagram.ts

export interface NodeComment {
  id: CommentID;
  nodeId: NodeID;
  userId: string;
  text: string;
  createdAt: Date;
  updatedAt?: Date;
}

// Add to DomainNode interface
export interface DomainNode {
  // ... existing fields
  comments?: NodeComment[];
}

// Add branded type
export type CommentID = string & { readonly brand: unique symbol };
```

#### 2. Run Code Generation

```bash
make codegen
```

This single command will:
- Generate Python domain models with the new `NodeComment` type
- Generate GraphQL schema with `NodeComment` type definition
- Generate Python GraphQL types (Strawberry) with proper decorators
- Generate frontend type mappings for converting between GraphQL and domain types
- Generate validation schemas and field configurations

#### 3. What Gets Generated

**Python Domain Models** (`dipeo/models/models.py`):
```python
class NodeComment(BaseModel):
    id: CommentID
    nodeId: NodeID  
    userId: str
    text: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
```

**GraphQL Schema** (`apps/server/src/dipeo_server/api/graphql/generated-schema.graphql`):
```graphql
type NodeCommentType {
  id: CommentID!
  nodeId: NodeID!
  userId: String!
  text: String!
  createdAt: DateTime!
  updatedAt: DateTime
}
```

**Python GraphQL Types** (`apps/server/src/dipeo_server/api/graphql/generated_types.py`):
```python
@strawberry.experimental.pydantic.type(NodeComment, all_fields=True)
class NodeCommentType:
    @strawberry.field
    def id(self) -> CommentID:
        return CommentID(str(self._pydantic_object.id))
```

**Frontend Type Mappings** (`apps/web/src/lib/graphql/types/generated-mappings.ts`):
```typescript
export function convertGraphQLNodeCommentToDomain(
  graphql: GraphQL.NodeComment
): Domain.NodeComment {
  return {
    id: graphql.id as Domain.CommentID,
    nodeId: graphql.nodeId as Domain.NodeID,
    userId: graphql.userId,
    text: graphql.text,
    createdAt: new Date(graphql.createdAt),
    updatedAt: graphql.updatedAt ? new Date(graphql.updatedAt) : undefined,
  };
}
```

## Benefits

1. **Single Source of Truth**: TypeScript models drive everything
2. **Type Safety**: End-to-end type safety from models to UI
3. **Consistency**: Guaranteed alignment between frontend and backend
4. **Speed**: Add a field once, get full-stack support automatically
5. **Less Error-Prone**: No manual synchronization needed

## Advanced Example: Adding a Complex Feature

For more complex features like adding a new node type:

```typescript
// dipeo/models/src/diagram.ts

export interface DatabaseNodeData extends BaseNodeData {
  connectionString: string;
  databaseType: DatabaseType;
  query?: string;
  timeout?: number;
}

export enum DatabaseType {
  POSTGRESQL = 'POSTGRESQL',
  MYSQL = 'MYSQL',
  MONGODB = 'MONGODB',
}

// Update NodeType enum
export enum NodeType {
  // ... existing types
  DATABASE = 'database',
}
```

Run `make codegen` and you'll get:
- Database node type in Python
- GraphQL types with proper enums
- Frontend converters handling the new node type
- Validation schemas for the new fields

## Best Practices

1. **Always start with TypeScript models** - They are the source of truth
2. **Use branded types** for IDs to ensure type safety
3. **Add JSDoc comments** - They'll be preserved in generated code
4. **Run `make codegen`** after any model changes
5. **Commit generated files** - They're part of the codebase

## Troubleshooting

If generation fails:
1. Check TypeScript syntax in model files
2. Ensure all imported types are defined
3. Look at generation script output for specific errors
4. Run individual generators to isolate issues:
   ```bash
   cd dipeo/models
   pnpm generate:schema        # Test schema extraction
   pnpm generate:graphql-schema # Test GraphQL generation
   ```

## Future Improvements

Potential enhancements to the generation pipeline:
- Auto-generate GraphQL resolvers
- Generate React hooks for mutations
- Generate test fixtures from types
- Add migration scripts for schema changes