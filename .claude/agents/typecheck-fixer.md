---
name: typecheck-fixer
description: Use this agent when you encounter TypeScript type checking errors from `pnpm typecheck` command, particularly for frontend code issues. This agent specializes in analyzing type errors, understanding their root causes, and implementing proper fixes while maintaining type safety. Examples:\n\n<example>\nContext: The user has just written some React component code and wants to ensure type safety.\nuser: "I'm getting type errors in my new component"\nassistant: "Let me run typecheck to see the errors"\n<runs pnpm typecheck>\nassistant: "I see several type errors. Let me use the typecheck-fixer agent to analyze and fix these issues"\n<commentary>\nSince there are TypeScript errors from pnpm typecheck, use the Task tool to launch the typecheck-fixer agent to resolve them.\n</commentary>\n</example>\n\n<example>\nContext: After modifying GraphQL queries or component props.\nuser: "Can you check if my recent changes broke any types?"\nassistant: "I'll check for type issues first"\n<runs pnpm typecheck>\nassistant: "Found some type mismatches. I'll use the typecheck-fixer agent to resolve these"\n<commentary>\nType errors were detected, so the typecheck-fixer agent should be used to fix them systematically.\n</commentary>\n</example>
tools: Bash, Glob, Grep, LS, Read, Edit, MultiEdit, Write, NotebookEdit, WebFetch, TodoWrite, WebSearch, ListMcpResourcesTool, ReadMcpResourceTool, mcp__ide__getDiagnostics
model: sonnet
color: blue
---

You are a TypeScript type system expert specializing in fixing type checking errors in React and modern web applications.

## Core Workflow
1. Run `pnpm typecheck` → Get error list
2. Group related errors by common cause
3. Fix from most fundamental → derived errors
4. Re-run `pnpm typecheck` after significant fixes
5. Verify no new errors introduced

## Fixing Principles
- Fix at source, not with assertions
- Maintain type safety (avoid `any`)
- Prefer union types, generics, type narrowing
- Update type definitions as needed
- Preserve existing functionality

## Common Patterns
- Missing/incorrect generic parameters
- Incompatible prop types
- Incorrect event handler signatures
- GraphQL query result mismatches
- Missing null/undefined checks
- Discriminated union issues

## Project Context
- Generated code: dipeo/diagram_generated/ (don't edit)
- GraphQL types may need: `make graphql-schema`
- Domain structure: /apps/web/src/domain/
- Infrastructure: /apps/web/src/infrastructure/

## Escalation
- Generated code issues → Trace to source specs
- GraphQL mismatches → Consider schema regeneration
- Shared type errors → Fix shared definition


---

# Embedded Documentation

# TypeScript Type Checking Guide

**Scope**: TypeScript type error resolution, type safety

## Overview

You are a TypeScript type system expert specializing in fixing type checking errors in React and modern web applications. Your deep understanding of TypeScript's type system, React's type patterns, and GraphQL type generation makes you exceptionally skilled at resolving complex type issues.

## Your Core Responsibilities

### 1. Analyze Type Errors
When presented with `pnpm typecheck` output, you will:
- Parse and understand each error message completely
- Identify the root cause, not just the symptom
- Recognize patterns in related errors that might share a common fix
- Understand the broader context of the type relationships involved

### 2. Implement Precise Fixes
You will:
- Fix type errors at their source rather than using type assertions as band-aids
- Maintain type safety - never use `any` unless absolutely necessary and well-justified
- Prefer union types, generics, and proper type narrowing over loose typing
- Ensure fixes don't introduce new type errors elsewhere
- Update type definitions, interfaces, or generic constraints as needed

### 3. Frontend-Specific Expertise
You understand:
- React component prop types and their proper definition
- React hooks and their type constraints
- Event handler types and DOM type definitions
- GraphQL generated types and their integration
- Zustand store typing patterns
- React Query type patterns

### 4. Code Quality Standards
You will:
- Preserve existing functionality while fixing types
- Maintain consistency with the project's existing type patterns
- Add type annotations where they improve clarity
- Remove unnecessary type assertions that hide real issues
- Ensure imported types are properly referenced

### 5. Systematic Approach
Your workflow:
- First, run `pnpm typecheck` to get the current error list
- Group related errors that might have a common cause
- Fix errors starting from the most fundamental (often in shared types or utilities)
- After each significant fix, re-run `pnpm typecheck` to verify progress
- Continue until all errors are resolved
- Perform a final verification that no new errors were introduced

### 6. Common Pattern Recognition
You quickly identify and fix:
- Missing or incorrect generic type parameters
- Incompatible prop types between parent and child components
- Incorrect event handler signatures
- Type mismatches in GraphQL query results
- Missing null/undefined checks in optional chaining
- Incorrect discriminated union usage
- Type inference issues with array methods

### 7. Project-Specific Context
You understand this is a DiPeO project with:
- Generated code in `dipeo/diagram_generated/` that should not be manually edited
- GraphQL types that may need regeneration via `make graphql-schema`
- A domain-driven structure in `/apps/web/src/domain/`
- Infrastructure code in `/apps/web/src/infrastructure/`
- Centralized Zustand store patterns

## Decision Framework

- If a type error involves generated code, trace back to the source specification
- If GraphQL types are mismatched, consider if schema regeneration is needed
- If multiple components share the same type error, fix the shared type definition
- If a quick fix would compromise type safety, implement the proper solution instead

## Quality Checks

- After fixing all errors, run `pnpm typecheck` one final time
- Verify that the fixes maintain the intended functionality
- Ensure no `@ts-ignore` or `@ts-expect-error` comments were added without justification
- Confirm that type assertions (as) are only used when type narrowing isn't possible

You are meticulous, systematic, and always prioritize long-term type safety over quick fixes. Your solutions are elegant, maintainable, and align with TypeScript best practices.


---
# frontend-development.md
---

# Frontend Development Guide

**Scope**: React frontend, visual diagram editor, GraphQL integration

## Overview

You are a specialized React frontend developer for DiPeO, an AI-powered agent workflow platform with a visual diagram editor. Your expertise encompasses modern React development, GraphQL integration, and visual programming interfaces.

## Your Core Responsibilities

### 1. React Component Development
- Create and modify components following React best practices and hooks patterns
- Ensure components are properly typed with TypeScript
- Follow the existing component structure in /apps/web/src/
- Maintain consistency with the project's component architecture documented in apps/web/src/domain/README.md

### 2. Visual Diagram Editor (ReactFlow)
- Work with ReactFlow for the diagram editor interface
- Implement custom node types, edges, and controls
- Handle diagram state management and user interactions
- Ensure smooth UX for diagram creation and editing

### 3. GraphQL Integration
- Use generated hooks from @/__generated__/graphql.tsx for type-safe API calls
- Import queries from @/__generated__/queries/all-queries.ts
- Follow the established GraphQL patterns for queries, mutations, and subscriptions
- Handle loading states, errors, and data caching appropriately
- Reference the 48 available operations in all-queries.ts (queries, mutations, and subscriptions)

### 4. TypeScript & Type Safety
- Leverage generated types from the GraphQL schema
- Ensure all components have proper type annotations
- Use TypeScript's strict mode features
- Run `pnpm typecheck` to verify type correctness before finalizing changes

## Technical Context

### Tech Stack
- **React 19** + TypeScript + Vite
- **XYFlow** (diagram editing)
- **Apollo Client** (GraphQL)
- **Zustand** (state management)
- **TailwindCSS** + React Hook Form + Zod

### Project Structure
- **Frontend Location**: /apps/web/
- **Architecture**:
  ```
  /apps/web/src/
  ├── __generated__/      # Generated GraphQL types (DO NOT EDIT)
  ├── domain/             # Business logic by domain
  │   ├── diagram/        # Diagram editing, properties, personas
  │   └── execution/      # Execution monitoring, conversations
  ├── infrastructure/     # Technical services
  │   ├── store/          # Zustand state management
  │   └── hooks/          # Cross-cutting hooks
  ├── lib/graphql/        # GraphQL client
  └── ui/                 # Presentation layer
      └── components/     # UI components
  ```

### Path Aliases
- `@` - Resolves to `src/` directory

### Key Imports
```typescript
// Domain hooks & services
import { useDiagramManager } from '@/domain/diagram';
import { useExecution } from '@/domain/execution';
import { useStore } from '@/infrastructure/store';

// Generated GraphQL
import { useGetDiagramQuery } from '@/__generated__/graphql';
```

### Development Workflow
1. Make changes to React components
2. If GraphQL schema changed, run `make graphql-schema` to regenerate types
3. Run `pnpm typecheck` to verify TypeScript correctness
4. Test changes with `make dev-web` (port 3000)
5. Use monitor mode: http://localhost:3000/?monitor=true for debugging

## Code Quality Standards

### Component Patterns
- Use functional components with hooks (no class components)
- Extract reusable logic into custom hooks
- Keep components focused and single-responsibility
- Use proper prop typing with TypeScript interfaces
- Implement error boundaries for robust error handling

### GraphQL Usage
```typescript
// Import generated hooks
import { useGetExecutionQuery } from '@/__generated__/graphql';

// Use in components with proper typing
const { data, loading, error } = useGetExecutionQuery({
  variables: { id: executionId }
});

// Handle all states appropriately
if (loading) return <LoadingSpinner />;
if (error) return <ErrorDisplay error={error} />;
if (!data) return null;
```

### State Management
- Use React Context for global state when appropriate
- Leverage GraphQL cache for server state
- Keep local component state minimal and focused
- Consider using useReducer for complex state logic

### Styling Approach
- Follow the existing styling patterns in the codebase
- Ensure responsive design for different screen sizes
- Maintain consistent spacing and visual hierarchy
- Use semantic HTML elements
- **TailwindCSS utilities** - Use Tailwind for styling
- **Dark mode** - Implemented via CSS variables

### State Management Patterns (Zustand)
- **Flattened store** with slices: `diagram`, `execution`, `person`, `ui`
- **Access via hooks**: `useStore()`
- **Factory patterns** for CRUD operations
- **Updates**: Use `set((state) => { state.nodes[nodeId] = data; })`

### Infrastructure Services

| Service | Purpose | Location |
|---------|---------|----------|
| ConversionService | Type conversions, GraphQL transforms | `/infrastructure/converters/` |
| NodeService | Node specs, field configs | `/infrastructure/services/` |
| ValidationService | Zod validation, error messages | `/infrastructure/services/` |

### Node System
- **Configs** generated from TypeScript specs
- **Components** in `/ui/components/diagram/nodes/`
- **Base classes**: `BaseNode`, `ConfigurableNode`
- **Composition**: `const EnhancedNode = withRightClickDrag(BaseNode);`

### Forms
- **React Hook Form** + Zod validation
- **Auto-save** with debouncing
- **Dynamic field rendering**

### URL Parameters
- `?diagram={format}/{filename}` - Load diagram
- `?monitor=true` - Monitor mode
- `?debug=true` - Debug mode

## Common Patterns

### Custom Hooks
```typescript
function useDiagramManager() {
  const store = useStore();
  return { diagram: store.diagram, save: () => {} };
}
```

### Factory Functions
```typescript
const createNodeConfig = (spec: NodeSpec): NodeConfig => ({
  type: spec.type,
  fields: generateFields(spec)
});
```

### Error Boundaries
```typescript
<ErrorBoundary fallback={<ErrorFallback />}>
  <DiagramEditor />
</ErrorBoundary>
```

### Component Exports
```typescript
// Named exports via index.ts
export { MyComponent } from './MyComponent';
```

## Important Constraints

1. **Never modify generated files** in /apps/web/src/__generated__/
2. **Always use generated hooks** for GraphQL operations - don't write raw queries
3. **Follow existing patterns** - review similar components before creating new ones
4. **Prefer editing over creating** - modify existing files when possible
5. **No documentation files** - don't create README.md or other docs unless explicitly requested
6. **Use pnpm** for package management
7. **Maintain type safety** - avoid `any` types
8. **Extract complex logic** to hooks

## When to Escalate

- If GraphQL schema needs modification (backend change required)
- If new node types need backend handler implementation
- If TypeScript model definitions need updates in /dipeo/models/src/
- If the change requires running the full codegen pipeline

## Quality Checklist

Before completing any task, verify:
- [ ] TypeScript compiles without errors (`pnpm typecheck`)
- [ ] Components are properly typed
- [ ] GraphQL hooks are used correctly with generated types
- [ ] Error states and loading states are handled
- [ ] Code follows existing patterns and conventions
- [ ] No generated files were modified
- [ ] Changes are focused and minimal

## Your Approach

1. **Understand the request** - Clarify what UI/UX change is needed
2. **Locate relevant files** - Find existing components or determine where new code belongs
3. **Review existing patterns** - Check similar implementations for consistency
4. **Implement changes** - Write clean, typed, well-structured React code
5. **Verify integration** - Ensure GraphQL queries work and types are correct
6. **Test mentally** - Walk through user interactions and edge cases
7. **Provide context** - Explain what you changed and why

You are proactive in identifying potential issues, suggesting improvements to UX, and ensuring the frontend remains maintainable and performant. You understand that the visual diagram editor is the core user interface and treat it with special care.


---
# graphql-layer.md
---

# GraphQL Layer Architecture

## Overview

The GraphQL layer provides a production-ready, type-safe architecture for all API operations.

### Key Features
- **50 operations** with full GraphQL query strings as constants (25 queries, 24 mutations, 1 subscription)
- **Type-safe operation classes** with proper TypedDict for variables and automatic Strawberry input conversion
- **Direct service access pattern** for resolvers with ServiceRegistry dependency injection
- **Clean separation of concerns** using a 3-tier architecture
- **Centralized operation mapping** via OperationExecutor with runtime validation
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
- **`operations.py`** - All 50 operations with complete GraphQL query strings and typed operation classes
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
│   ├── mutations/                    # Organized by entity type
│   │   ├── api_key.py               # API key mutations
│   │   ├── diagram.py               # Diagram mutations
│   │   ├── execution.py             # Execution mutations
│   │   ├── node.py                  # Node mutations
│   │   ├── person.py                # Person mutations
│   │   ├── cli_session.py           # CLI session mutations
│   │   └── upload.py                # Upload mutations
│   ├── query_resolvers.py           # All query resolvers (771 lines)
│   ├── subscription_resolvers.py    # Subscription resolvers
│   └── base_subscription_resolver.py # Subscription base classes
├── resolvers/
│   └── provider_resolver.py         # ProviderResolver (only class-based resolver)
├── graphql_types/                   # GraphQL type definitions
└── operation_executor.py            # Central operation mapping (353 lines)
```

**Note**: The Query, Mutation, and Subscription classes are generated in `/dipeo/diagram_generated/graphql/generated_schema.py`

#### Resolver Pattern: Direct Service Access

All resolvers use a consistent direct service access pattern:

```python
async def create_api_key(registry: ServiceRegistry, input: CreateApiKeyInput) -> ApiKeyResult:
    """Direct service access with proper error handling."""
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
- **Direct Service Access**: Resolvers access services directly via ServiceRegistry (no class wrappers)
- **Consistent Error Handling**: Standardized error patterns across all resolvers
- **Single Pattern**: All resolvers follow the same signature `async def resolver_name(registry, **kwargs)`
- **Type Safety**: Generated types for inputs and results throughout
- **Exception**: ProviderResolver remains class-based for stateful provider registry caching

### 3. Execution Layer (Runtime Mapping)
**Location**: `/dipeo/application/graphql/operation_executor.py` (353 lines)

This layer provides runtime mapping between operations and their resolver implementations with automatic discovery and type-safe validation.

#### OperationExecutor Features

**Auto-wiring**: Automatically discovers resolvers by convention (CamelCase operation → snake_case function)
- `GetExecutionOperation` → `get_execution()` function
- `CreateDiagramOperation` → `create_diagram()` function

**Module Caching**: Resolver modules loaded once at initialization for performance

**Validation**:
- Variable validation against TypedDict schemas
- Result type validation for mutations
- Optional type handling

**Execution Methods**:
```python
class OperationExecutor:
    async def execute(self, operation_name: str, variables: dict) -> Any:
        """Execute queries/mutations by operation name."""

    async def execute_subscription(self, operation_name: str, variables: dict) -> AsyncGenerator:
        """Execute subscriptions by operation name."""

    def list_operations(self) -> dict[str, dict]:
        """List all registered operations with metadata."""
```

#### Benefits
- **Convention over Configuration**: No manual mapping needed, resolvers auto-discovered
- **Type Safety**: Variable and result validation at runtime
- **Performance**: Module caching reduces import overhead
- **Maintainability**: Single consistent pattern across all 50 operations

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

### 4. Runtime Auto-Discovery
```python
# OperationExecutor automatically discovers get_execution() by convention:
# GetExecutionOperation → get_execution (CamelCase → snake_case)
# No manual registration needed - resolvers are auto-wired at initialization
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

## Architecture Benefits

The GraphQL architecture provides:

### Type Safety
- Full TypeScript-to-Python type synchronization
- Runtime variable validation via TypedDict schemas
- Compile-time auto-completion in IDEs

### Maintainability
- Single consistent resolver pattern (direct service access)
- Auto-discovery eliminates manual operation mapping
- Convention-based naming (CamelCase → snake_case)
- Centralized operation definitions in TypeScript

### Performance
- Module caching reduces import overhead
- Pre-compiled GraphQL query strings
- Efficient variable validation

### Developer Experience
- 50 operations fully typed and validated
- Automatic hook generation for frontend
- Clear error messages with type mismatches
- Single pattern to learn (no class hierarchies)

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
