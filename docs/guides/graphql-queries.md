# GraphQL Queries Developer Guide

## Overview

DiPeO uses a centralized, type-safe GraphQL operations system that eliminates inline query strings and ensures consistency across the frontend. All GraphQL operations are defined in TypeScript and automatically generated into both query strings and React hooks.

## Architecture

### Flow

```
TypeScript Definitions → Code Generation → GraphQL Operations → React Hooks & Python Classes
```

1. **Source**: `/dipeo/models/src/frontend/query-definitions/*.ts`
2. **Generated Queries**: `/apps/web/src/__generated__/queries/all-queries.ts`
3. **React Hooks**: `/apps/web/src/__generated__/graphql.tsx`
4. **Python Operations**: `/dipeo/diagram_generated/graphql/operations.py`

## Adding New Operations

### Step 1: Define the Operation

Create or update a query definition file in `/dipeo/models/src/frontend/query-definitions/`:

```typescript
// executions.ts
import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const executionQueries: EntityQueryDefinitions = {
  entity: 'Execution',
  queries: [
    {
      name: 'GetExecution',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'execution',
          args: [
            { name: 'id', value: 'id', isVariable: true }
          ],
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'diagram_id' },
            { name: 'started_at' },
            { name: 'ended_at' },
            { name: 'error' },
            { name: 'node_states' },
            { name: 'node_outputs' }
          ]
        }
      ]
    }
  ]
}
```

### Step 2: Build TypeScript Models

```bash
cd dipeo/models
pnpm build
```

### Step 3: Generate GraphQL Operations

```bash
make codegen
make apply-syntax-only
```

### Step 4: Update GraphQL Schema

```bash
make graphql-schema
```

### Step 5: Use in Components

```typescript
import { useGetExecutionQuery } from '@/__generated__/graphql';

function ExecutionMonitor({ executionId }: { executionId: string }) {
  const { data, loading, error } = useGetExecutionQuery({
    variables: { id: executionId },
    pollInterval: 1000 // Real-time updates
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <h2>Execution {data.execution.id}</h2>
      <p>Status: {data.execution.status}</p>
    </div>
  );
}
```

## Operation Types

### Queries

For fetching data:

```typescript
{
  name: 'GetDiagram',
  type: QueryOperationType.QUERY,
  variables: [
    { name: 'id', type: 'ID', required: true }
  ],
  fields: [/* ... */]
}
```

### Mutations

For modifying data:

```typescript
{
  name: 'CreateDiagram',
  type: QueryOperationType.MUTATION,
  variables: [
    { name: 'input', type: 'CreateDiagramInput', required: true }
  ],
  fields: [/* ... */]
}
```

### Subscriptions

For real-time updates:

```typescript
{
  name: 'ExecutionUpdates',
  type: QueryOperationType.SUBSCRIPTION,
  variables: [
    { name: 'executionId', type: 'ID', required: true }
  ],
  fields: [/* ... */]
}
```

## Field Definition Patterns

### Basic Fields

```typescript
fields: [
  { name: 'id' },
  { name: 'name' },
  { name: 'created_at' }
]
```

### Nested Objects

```typescript
fields: [
  {
    name: 'user',
    fields: [
      { name: 'id' },
      { name: 'email' },
      { name: 'profile', fields: [
        { name: 'avatar' },
        { name: 'bio' }
      ]}
    ]
  }
]
```

### Fields with Arguments

```typescript
fields: [
  {
    name: 'executions',
    args: [
      { name: 'filter', value: 'filter', isVariable: true },
      { name: 'limit', value: 10 },
      { name: 'offset', value: 'offset', isVariable: true }
    ],
    fields: [/* ... */]
  }
]
```

## Variable Types

### Scalar Types
- `ID` - Unique identifier
- `String` - Text data
- `Int` - Integer numbers
- `Float` - Decimal numbers
- `Boolean` - True/false

### Input Types
- `CreateDiagramInput`
- `UpdateNodeInput`
- `ExecutionFilterInput`

### Custom Types
- `JSON` - Arbitrary JSON data
- `DateTime` - ISO 8601 timestamps

## Generated Hook Variants

For each query, multiple hooks are generated:

```typescript
// Standard query hook
useGetDiagramQuery()

// Lazy query (manual execution)
useGetDiagramLazyQuery()

// Suspense-enabled query
useGetDiagramSuspenseQuery()
```

For mutations:

```typescript
const [createDiagram, { data, loading, error }] = useCreateDiagramMutation();

// Execute mutation
await createDiagram({
  variables: { input: diagramData }
});
```

## Best Practices

### 1. Naming Conventions

- Queries: `Get*` or `List*`
- Mutations: `Create*`, `Update*`, `Delete*`
- Subscriptions: `*Updates` or `*Changed`

### 2. Field Selection

Only request fields you need:

```typescript
fields: [
  { name: 'id' },
  { name: 'name' },
  // Don't include heavy fields unless needed
  // { name: 'large_content' }
]
```

### 3. Error Handling

```typescript
const { data, loading, error } = useGetDiagramQuery({
  variables: { id },
  onError: (error) => {
    console.error('Failed to fetch diagram:', error);
    showNotification({ type: 'error', message: error.message });
  }
});
```

### 4. Optimistic Updates

```typescript
const [updateNode] = useUpdateNodeMutation({
  optimisticResponse: {
    updateNode: {
      __typename: 'Node',
      id: nodeId,
      ...optimisticData
    }
  }
});
```

### 5. Polling vs Subscriptions

- Use polling for simple periodic updates
- Use subscriptions for real-time, event-driven updates

```typescript
// Polling
useGetExecutionQuery({
  variables: { id },
  pollInterval: 2000
});

// Subscription
useExecutionUpdatesSubscription({
  variables: { executionId }
});
```

## Troubleshooting

### Common Issues

#### 1. Generated hooks not found

```bash
# Regenerate everything
make codegen
make apply-syntax-only
make graphql-schema
```

#### 2. Type mismatches

```bash
# Check TypeScript types
cd apps/web
pnpm typecheck
```

#### 3. Missing fields in response

- Verify field is included in query definition
- Check GraphQL schema has the field
- Ensure backend returns the field

#### 4. Duplicate operation names

- Operation names must be globally unique
- Check all query definition files for conflicts

### Debugging Tools

1. **GraphQL Playground**: http://localhost:8000/graphql
2. **Apollo DevTools**: Browser extension for inspecting cache
3. **Network tab**: Check actual GraphQL requests/responses

## Migration Guide

### From Inline Queries

Before:
```typescript
const GET_DIAGRAM = gql`
  query GetDiagram($id: ID!) {
    diagram(id: $id) {
      id
      name
    }
  }
`;

const { data } = useQuery(GET_DIAGRAM, { variables: { id } });
```

After:
```typescript
import { useGetDiagramQuery } from '@/__generated__/graphql';

const { data } = useGetDiagramQuery({ variables: { id } });
```

### Benefits of Migration

1. **Type Safety**: Full TypeScript types for variables and results
2. **Consistency**: Single source of truth for all operations
3. **Maintainability**: Centralized query definitions
4. **Performance**: Optimized query generation
5. **Developer Experience**: Auto-completion and inline documentation

## Advanced Topics

### Fragment Reuse

Define reusable field sets:

```typescript
const userFields = [
  { name: 'id' },
  { name: 'email' },
  { name: 'name' }
];

// Use in multiple queries
fields: [
  { name: 'created_by', fields: userFields },
  { name: 'updated_by', fields: userFields }
]
```

### Conditional Fields

Use variables to conditionally include fields:

```typescript
variables: [
  { name: 'includeMetrics', type: 'Boolean' }
],
fields: [
  { name: 'id' },
  { 
    name: 'metrics',
    condition: 'includeMetrics',
    fields: [/* ... */]
  }
]
```

### Batch Operations

Group related operations:

```typescript
const [
  createNode,
  { data: createData }
] = useCreateNodeMutation();

const [
  connectNodes,
  { data: connectData }
] = useConnectNodesMutation();

// Execute in sequence
await createNode({ variables: nodeData });
await connectNodes({ variables: connectionData });
```

## File Structure

```
/dipeo/models/src/frontend/query-definitions/
├── index.ts           # Exports all query definitions
├── types.ts           # TypeScript interfaces
├── api-keys.ts        # API key operations
├── cli-sessions.ts    # CLI session operations
├── conversations.ts   # Conversation operations
├── diagrams.ts        # Diagram CRUD operations
├── executions.ts      # Execution monitoring
├── files.ts           # File operations
├── formats.ts         # Format conversion
├── nodes.ts           # Node operations
├── persons.ts         # Person/agent operations
├── prompts.ts         # Prompt file operations
├── providers.ts       # Integration providers
└── system.ts          # System info operations
```

## Python Usage

### Generated Operations

All GraphQL operations are also generated for Python in `/dipeo/diagram_generated/graphql/operations.py`:

```python
from dipeo.diagram_generated.graphql.operations import (
    ExecuteDiagramOperation,
    GetExecutionOperation,
    RegisterCliSessionOperation,
    # ... other operations
)
```

### Using Operation Classes

Each operation class provides:
- `query`: The GraphQL query string
- `get_query()`: Method to retrieve the query
- `get_variables_dict()`: Helper to build variables dictionary

#### Example: Executing a Diagram

```python
from dipeo.diagram_generated.graphql.operations import ExecuteDiagramOperation

# Build variables
variables = ExecuteDiagramOperation.get_variables_dict(
    input={
        "diagram_id": "example_diagram",
        "variables": {"param1": "value1"},
        "use_unified_monitoring": True
    }
)

# Make GraphQL request
response = requests.post(
    "http://localhost:8000/graphql",
    json={
        "query": ExecuteDiagramOperation.get_query(),
        "variables": variables
    }
)
```

#### Example: Querying Execution Status

```python
from dipeo.diagram_generated.graphql.operations import GetExecutionOperation

# Build variables
variables = GetExecutionOperation.get_variables_dict(id=execution_id)

# Make request
response = requests.post(
    "http://localhost:8000/graphql",
    json={
        "query": GetExecutionOperation.get_query(),
        "variables": variables
    }
)

# Parse response
result = response.json()
execution = result["data"]["execution"]
print(f"Status: {execution['status']}")
```

### Input Types

Input types are available from `/dipeo/diagram_generated/graphql/inputs.py`:

```python
from dipeo.diagram_generated.graphql.inputs import (
    ExecuteDiagramInput,
    RegisterCliSessionInput,
    UpdateNodeStateInput,
    # ... other input types
)

# Note: When calling get_variables_dict(), pass plain dictionaries
# matching the input structure, not Strawberry input objects
input_dict = {
    "diagram_id": "example",
    "variables": {},
    "debug_mode": True
}
variables = ExecuteDiagramOperation.get_variables_dict(input=input_dict)
```

### Available Operations

The generated operations module includes:
- **Queries** (23): GetExecution, ListExecutions, GetDiagram, etc.
- **Mutations** (21): ExecuteDiagram, CreateNode, UpdateNode, etc.
- **Subscriptions** (1): ExecutionUpdates

Each operation follows the naming convention:
- Query: `GetExecutionOperation`, `ListExecutionsOperation`
- Mutation: `ExecuteDiagramOperation`, `CreateNodeOperation`
- Subscription: `ExecutionUpdatesSubscription`

### Migration from Inline Queries

Before:
```python
query = """
    mutation ExecuteDiagram($diagramId: ID!, $variables: JSON) {
        execute_diagram(diagram_id: $diagramId, variables: $variables) {
            success
            execution_id
        }
    }
"""
variables = {"diagramId": "example", "variables": {}}
```

After:
```python
from dipeo.diagram_generated.graphql.operations import ExecuteDiagramOperation

variables = ExecuteDiagramOperation.get_variables_dict(
    input={"diagram_id": "example", "variables": {}}
)
query = ExecuteDiagramOperation.get_query()
```

## Summary

The GraphQL operations system provides:
- **Type safety** throughout the stack (frontend and backend)
- **Single source of truth** for all operations
- **Automated code generation** reducing boilerplate
- **Consistent patterns** across TypeScript and Python
- **Better developer experience** with auto-completion
- **Cross-language consistency** from TypeScript definitions

Follow this guide when adding new GraphQL operations to maintain consistency and leverage the full power of the type-safe system.
