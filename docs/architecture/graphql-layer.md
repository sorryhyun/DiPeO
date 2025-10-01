# GraphQL Layer Architecture

## Overview

The GraphQL layer provides a production-ready, type-safe architecture for all API operations.

### Key Features
- **45 operations** with full GraphQL query strings as constants (23 queries, 21 mutations, 1 subscription)
- **Type-safe operation classes** with proper TypedDict for variables and automatic Strawberry input conversion
- **Well-structured resolver implementations** following consistent patterns
- **Clean separation of concerns** using a 3-tier architecture
- **ServiceRegistry integration** for dependency injection throughout
- **Envelope system integration** for standardized data flow

## Architecture Overview

The GraphQL layer uses a clean 3-tier architecture that separates code generation, application logic, and execution:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Generated Layer                         │
│  (Automated from TypeScript - DO NOT EDIT)                     │
├─────────────────────────────────────────────────────────────────┤
│                      Application Layer                         │
│  (Manual implementation - Business Logic)                      │
├─────────────────────────────────────────────────────────────────┤
│                      Execution Layer                           │
│  (Runtime mapping and validation)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Generated Layer (Automated)
**Location**: `/dipeo/diagram_generated/graphql/`

This layer is completely generated from TypeScript query definitions and provides the foundation for type-safe GraphQL operations.

#### Key Files
- **`operations.py`** - All 45 operations with complete GraphQL query strings and typed operation classes
- **`inputs.py`** - Generated Strawberry input types
- **`results.py`** - Generated result types for consistent response formats
- **`domain_types.py`** - Generated domain types mapping to internal models
- **`enums.py`** - Generated enum types
- **`generated_schema.py`** - Generated Query, Mutation, and Subscription classes with field resolvers

#### operations.py Structure
```python
# GraphQL query strings as constants
EXECUTE_DIAGRAM_MUTATION = """mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
  execute_diagram(input: $input) {
    success
    execution_id
    message
    error
  }
}"""

# Typed operation classes with automatic variable handling
class ExecuteDiagramOperation:
    query = EXECUTE_DIAGRAM_MUTATION
    
    class Variables(TypedDict):
        input: ExecuteDiagramInput
    
    @classmethod
    def get_query(cls) -> str:
        return cls.query
    
    @classmethod 
    def get_variables_dict(cls, **kwargs) -> dict:
        # Automatic conversion from dict to Strawberry input objects
        return convert_to_strawberry_inputs(kwargs, cls.Variables)
```

#### Benefits
- **Type Safety**: Full typing annotations for all operations
- **Consistency**: Single source of truth for all GraphQL operations
- **Automatic Updates**: Regenerated when TypeScript definitions change
- **Cross-Language**: Same operations available in both TypeScript and Python

### 2. Application Layer (Manual Implementation)
**Location**: `/dipeo/application/graphql/`

This layer contains the business logic and resolver implementations that handle the actual GraphQL requests.

#### File Organization
```
/dipeo/application/graphql/
├── schema/
│   ├── mutations/           # Organized by entity type
│   │   ├── api_key.py      # API key mutations
│   │   ├── diagram.py      # Diagram mutations
│   │   ├── execution.py    # Execution mutations
│   │   ├── node.py         # Node mutations
│   │   ├── person.py       # Person mutations
│   │   ├── cli_session.py  # CLI session mutations
│   │   └── upload.py       # Upload mutations
│   ├── query_resolvers.py  # Standalone query resolvers
│   └── subscription_resolvers.py  # Subscription resolvers
├── resolvers/              # Business logic resolvers
│   ├── diagram.py         # DiagramResolver
│   ├── execution.py       # ExecutionResolver
│   └── person.py          # PersonResolver
├── types/                 # GraphQL type definitions
└── operation_executor.py  # Central operation mapping
```

**Note**: The Query, Mutation, and Subscription classes are now generated in `/dipeo/diagram_generated/graphql/generated_schema.py`

#### Resolver Patterns
All resolvers follow consistent patterns with proper error handling and ServiceRegistry integration:

```python
async def create_api_key(registry: ServiceRegistry, input: CreateApiKeyInput) -> ApiKeyResult:
    """Well-structured resolver with proper service resolution and error handling."""
    try:
        service = registry.resolve(API_KEY_SERVICE)
        result = await service.create_api_key(
            label=input.label,
            service=input.service,
            encrypted_key=input.encrypted_key
        )
        return ApiKeyResult.success_result(
            data=result, 
            message=f"API key '{input.label}' created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        return ApiKeyResult.error_result(error=str(e))
```

#### Key Characteristics
- **ServiceRegistry Integration**: All resolvers use dependency injection
- **Consistent Error Handling**: Standardized error patterns across all resolvers
- **Clean Separation**: Business logic separated from GraphQL concerns
- **Type Safety**: Use generated types for inputs and results

### 3. Execution Layer (Runtime Mapping)
**Location**: `/dipeo/application/graphql/operation_executor.py`

This layer provides runtime mapping between operations and their resolver implementations with type-safe validation.

#### OperationExecutor Structure
```python
class OperationExecutor:
    """Type-safe execution engine mapping operations to resolvers."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.operation_mapping = {
            # Queries
            "GetExecution": self._execute_get_execution,
            "ListExecutions": self._execute_list_executions,
            "GetDiagram": self._execute_get_diagram,
            # Mutations  
            "ExecuteDiagram": self._execute_execute_diagram,
            "CreateNode": self._execute_create_node,
            "UpdateNode": self._execute_update_node,
            # Subscriptions
            "ExecutionUpdates": self._execute_execution_updates,
            # ... all 45 operations mapped
        }
    
    async def execute_operation(self, operation_name: str, variables: dict) -> Any:
        """Execute operation with validation and error handling."""
        if operation_name not in self.operation_mapping:
            raise ValueError(f"Unknown operation: {operation_name}")
        
        # Validate variables against operation schema
        self._validate_variables(operation_name, variables)
        
        # Execute with proper error handling
        try:
            resolver = self.operation_mapping[operation_name]
            result = await resolver(variables)
            return self._validate_result(operation_name, result)
        except Exception as e:
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
```

#### Benefits
- **Type Safety**: Variable validation against operation schemas
- **Centralized Mapping**: Single registry for all operations
- **Error Handling**: Consistent error handling patterns
- **Service Injection**: ServiceRegistry available to all resolvers

## Integration with DiPeO Systems

### Event System Integration
The GraphQL layer integrates seamlessly with DiPeO's event-driven architecture:

```python
# GraphQL subscriptions use the unified EventBus
async def execution_updates(execution_id: str) -> AsyncGenerator[ExecutionUpdate, None]:
    event_bus = registry.resolve(EVENT_BUS_SERVICE)
    
    async for event in event_bus.subscribe(ExecutionEvent):
        if event.execution_id == execution_id:
            yield ExecutionUpdate(
                execution_id=event.execution_id,
                status=event.status,
                node_states=event.node_states
            )
```

### Envelope System Integration
All GraphQL resolvers work with DiPeO's Envelope system for standardized data flow:

```python
async def get_node_output(node_id: str, execution_id: str) -> NodeOutput:
    execution_service = registry.resolve(EXECUTION_SERVICE)
    envelope = await execution_service.get_node_output(execution_id, node_id)
    
    return NodeOutput(
        node_id=node_id,
        content=envelope.body,
        content_type=envelope.content_type,
        metadata=envelope.metadata
    )
```

### Service Registry Integration
The ServiceRegistry pattern provides clean dependency injection throughout the GraphQL layer:

```python
# Services are injected, never directly instantiated
async def execute_diagram(registry: ServiceRegistry, input: ExecuteDiagramInput) -> ExecutionResult:
    execution_service = registry.resolve(EXECUTION_SERVICE)
    diagram_service = registry.resolve(DIAGRAM_SERVICE)
    
    # Business logic using injected services
    diagram = await diagram_service.get_diagram(input.diagram_id)
    execution = await execution_service.start_execution(diagram, input.variables)
    
    return ExecutionResult.success_result(execution_id=execution.id)
```

## Code Generation Workflow

The GraphQL layer is maintained through DiPeO's code generation pipeline:

### 1. TypeScript Definition (Source)
```typescript
// /dipeo/models/src/frontend/query-definitions/executions.ts
export const executionQueries: EntityQueryDefinitions = {
  entity: 'Execution',
  queries: [
    {
      name: 'GetExecution',
      type: QueryOperationType.QUERY,
      variables: [{ name: 'id', type: 'ID', required: true }],
      fields: [
        {
          name: 'execution',
          args: [{ name: 'id', value: 'id', isVariable: true }],
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'diagram_id' }
          ]
        }
      ]
    }
  ]
}
```

### 2. Generated Operations (Automated)
```python
# /dipeo/diagram_generated/graphql/operations.py (Generated)
GET_EXECUTION_QUERY = """query GetExecution($id: ID!) {
  execution(id: $id) {
    id
    status
    diagram_id
  }
}"""

class GetExecutionOperation:
    query = GET_EXECUTION_QUERY
    class Variables(TypedDict):
        id: str
```

### 3. Manual Implementation (Business Logic)
```python
# /dipeo/application/graphql/schema/query_resolvers.py (Manual)
async def get_execution(registry: ServiceRegistry, id: str) -> ExecutionResult:
    service = registry.resolve(EXECUTION_SERVICE)
    execution = await service.get_execution(id)
    return ExecutionResult.success_result(data=execution)
```

### 4. Runtime Registration (Automated)
```python
# /dipeo/application/graphql/operation_executor.py (Manual)
self.operation_mapping = {
    "GetExecution": self._execute_get_execution,
    # ... other operations
}
```

## Performance and Scalability

### Type-Safe Operations
- **Compile-time validation** of operation variables and results
- **Auto-completion** in IDEs for all operations
- **Reduced runtime errors** through comprehensive typing

### Efficient Query Generation
- **Pre-compiled queries** stored as constants (no runtime parsing)
- **Optimized field selection** based on TypeScript definitions
- **Minimal network overhead** with precise field requests

### Subscription Performance
- **Event-driven subscriptions** using unified EventBus
- **Selective filtering** to reduce unnecessary updates
- **WebSocket efficiency** through GraphQL-WS protocol

## Testing Strategy

The generated operations.py enables comprehensive testing:

### Operation Testing
```python
def test_execute_diagram_operation():
    # Test variable construction
    variables = ExecuteDiagramOperation.get_variables_dict(
        input={"diagram_id": "test", "variables": {}}
    )
    assert "input" in variables
    assert variables["input"]["diagram_id"] == "test"
    
    # Test query retrieval
    query = ExecuteDiagramOperation.get_query()
    assert "ExecuteDiagram" in query
    assert "$input: ExecuteDiagramInput!" in query
```

### Resolver Testing
```python
async def test_execute_diagram_resolver():
    registry = create_test_registry()
    input_data = ExecuteDiagramInput(diagram_id="test", variables={})
    
    result = await execute_diagram(registry, input_data)
    
    assert result.success is True
    assert result.execution_id is not None
```

### Integration Testing
```python
async def test_graphql_operation_end_to_end():
    # Use generated operations for integration tests
    response = await graphql_client.execute(
        ExecuteDiagramOperation.get_query(),
        ExecuteDiagramOperation.get_variables_dict(
            input={"diagram_id": "integration_test", "variables": {}}
        )
    )
    assert response["data"]["execute_diagram"]["success"] is True
```

## Migration Benefits

The completed GraphQL architecture provides significant benefits over the previous implementation:

### Before (Inline Queries)
```python
# Scattered query definitions
EXECUTE_QUERY = """
    mutation ExecuteDiagram($diagramId: ID!, $variables: JSON) {
        execute_diagram(diagram_id: $diagramId, variables: $variables) {
            success
            execution_id
        }
    }
"""

# Manual variable construction with potential errors
variables = {"diagramId": diagram_id, "variables": execution_vars}
```

### After (Generated Operations)
```python
# Type-safe operation with validation
variables = ExecuteDiagramOperation.get_variables_dict(
    input={"diagram_id": diagram_id, "variables": execution_vars}
)
query = ExecuteDiagramOperation.get_query()

# Automatic input type conversion and validation
```

### Key Improvements
1. **Type Safety**: Full TypeScript types throughout the stack
2. **Consistency**: Single source of truth for all operations
3. **Maintainability**: Centralized operation definitions
4. **Developer Experience**: Auto-completion and inline documentation
5. **Error Reduction**: Compile-time validation prevents runtime errors

## Developer Guide

### Adding New GraphQL Operations

1. **Add definition** to `/dipeo/models/src/frontend/query-definitions/[entity].ts`
2. **Build models**: `cd dipeo/models && pnpm build`
3. **Generate queries**: `make codegen`
4. **Apply changes**: `make apply-test`
5. **Update GraphQL schema**: `make graphql-schema`

### Query Definition Structure

```typescript
// In /dipeo/models/src/frontend/query-definitions/[entity].ts
export const entityQueries: EntityQueryDefinitions = {
  entity: 'EntityName',
  queries: [
    {
      name: 'GetEntity',
      type: QueryOperationType.QUERY,
      variables: [{ name: 'id', type: 'ID', required: true }],
      fields: [/* GraphQL fields */]
    }
  ]
}
```

### File Structure

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

## Frontend Usage

### Using Generated Hooks

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

### Generated Hook Variants

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

### Field Definition Patterns

#### Basic Fields
```typescript
fields: [
  { name: 'id' },
  { name: 'name' },
  { name: 'created_at' }
]
```

#### Nested Objects
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

#### Fields with Arguments
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

## Python Usage

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

### Available Operations

The generated operations module includes:
- **Queries** (23): GetExecution, ListExecutions, GetDiagram, etc.
- **Mutations** (21): ExecuteDiagram, CreateNode, UpdateNode, etc.
- **Subscriptions** (1): ExecutionUpdates

Each operation follows the naming convention:
- Query: `GetExecutionOperation`, `ListExecutionsOperation`
- Mutation: `ExecuteDiagramOperation`, `CreateNodeOperation`
- Subscription: `ExecutionUpdatesSubscription`

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
const [createNode, { data: createData }] = useCreateNodeMutation();
const [connectNodes, { data: connectData }] = useConnectNodesMutation();

// Execute in sequence
await createNode({ variables: nodeData });
await connectNodes({ variables: connectionData });
```

## Summary

The GraphQL layer provides a mature, production-ready architecture that balances:

- **Type Safety**: Comprehensive typing throughout the entire stack
- **Maintainability**: Clean separation of concerns and consistent patterns
- **Performance**: Efficient query generation and execution
- **Developer Experience**: Auto-completion, validation, and clear error messages
- **Scalability**: Event-driven architecture with proper dependency injection

The 3-tier architecture ensures that generated code stays separate from business logic while maintaining type safety and consistency across the entire system.
