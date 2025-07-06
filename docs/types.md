# DiPeO Domain Model Conversion Analysis

## Overview

DiPeO uses TypeScript domain models in `@dipeo/models/` as the single source of truth. These models are automatically converted to Python for the backend and integrated with the frontend through a sophisticated code generation pipeline.

## Domain Model Architecture

### Source of Truth: TypeScript Models

The TypeScript domain models are located in `dipeo/models/src/`:
- **diagram.ts**: Core diagram structure (nodes, arrows, handles, persons)
- **execution.ts**: Execution state and token usage tracking
- **conversation.ts**: Message formats and conversation state
- **integration.ts**: External service configurations (LLM, APIs)
- **conversions.ts**: Type conversion utilities
- **diagram-utils.ts**: TypeScript-only utilities for diagram manipulation
- **graphql-conversions.ts**: Conversions between GraphQL and store format representations
- **service-utils.ts**: Utilities for distinguishing between LLM and non-LLM services

Key features:
- Uses branded types for type-safe IDs (e.g., `NodeID`, `PersonID`)
- Defines enums for fixed value sets
- Provides interfaces for data structures
- Includes utility functions for type conversions
- Support for tools (web search, image generation) and hooks (shell, webhook, Python, file)

## Code Generation Pipeline

### 1. TypeScript → Schema JSON

**Script**: `dipeo/models/scripts/generate-schema.ts`
- Uses ts-morph to parse TypeScript AST
- Extracts interfaces, enums, and type aliases
- Generates `__generated__/schemas.json`

### 2. Schema JSON → Python Models

**Script**: `dipeo/models/scripts/generate-python.ts`
- Reads schema JSON
- Generates Pydantic models with proper type mappings
- Outputs to `packages/python/dipeo_domain/src/dipeo_domain/models.py`

Type mapping examples:
- `string` → `str`
- `number` → `float` (or `int` for specific fields)
- `T[]` → `List[T]`
- Branded types → `NewType('TypeName', str)`
- Enums → `class EnumName(str, Enum)`

### 3. TypeScript → Python Conversions

**Script**: `dipeo/models/scripts/generate-conversions.ts`
- Extracts NODE_TYPE_MAP from conversions.ts
- Generates Python conversion utilities
- Outputs to `packages/python/dipeo_domain/src/dipeo_domain/conversions.py`

## Backend Integration

### Python Models Usage

The generated Python models are used throughout the backend:

1. **Domain Layer** (`packages/python/dipeo_domain/`)
   - Provides type-safe domain models
   - Ensures data validation via Pydantic
   - Used by domain services for business logic

2. **GraphQL Layer** (`apps/server/src/dipeo_server/api/graphql/`)
   - Imports domain models directly:
     ```python
     from dipeo_domain import (
         DomainDiagram,
         DomainNode,
         NodeType,
         ExecutionState
     )
     ```
   - Converts Pydantic models to Strawberry GraphQL types
   - Uses `strawberry.experimental.pydantic` integration

3. **Application Layer**
   - Uses domain models for request/response validation
   - Ensures type safety across service boundaries

4. **Domain Services** (`packages/python/dipeo_domain/domains/`)
   - Specialized domain services for different node types:
     - api, apikey, conversation, db, diagram, execution, file, text, validation
   - Port interfaces and adapters for clean architecture
   - Utility modules like `handle_utils.py` and `service_utils.py`

### GraphQL Schema Generation

The GraphQL schema is generated from Python Strawberry server (code-first approach):

1. Python domain models are decorated with Strawberry types
2. Schema is exported via `apps/server/schema.graphql`
3. The schema preserves snake_case field names (auto_camel_case=False)
4. Branded types are exposed as scalar types in GraphQL

## Frontend Integration

### Direct TypeScript Import

The frontend directly imports TypeScript domain models:
```typescript
import {
  StartNodeData,
  NodeType,
  HandleDirection
} from "@dipeo/models";
```

### GraphQL Code Generation

**Configuration**: `apps/web/codegen.yml`
- Uses `@graphql-codegen` to generate TypeScript types from GraphQL schema
- Maps GraphQL scalars back to branded types from `@dipeo/models`
- Reuses enums from the domain models package

Key mappings:
```yaml
scalars:
  NodeID: "@dipeo/models#NodeID"
  HandleID: "@dipeo/models#HandleID"
enumValues:
  NodeType: "@dipeo/models#NodeType"
  HandleDirection: "@dipeo/models#HandleDirection"
```

### Frontend Usage Pattern

1. Domain models are extended with UI-specific properties:
   ```typescript
   type WithUI<T> = T & { 
     flipped?: boolean; 
     [key: string]: unknown;
   };
   
   export type PersonJobNodeData = WithUI<DomainPersonJobNodeData>;
   ```

2. GraphQL types are re-exported for consistency:
   ```typescript
   import type { Node as DomainNode } from '@/graphql/types';
   export type { DomainNode };
   ```

## Data Flow Summary

```
┌─────────────────────────┐
│  TypeScript Domain      │
│  Models (Source)        │
└───────────┬─────────────┘
            │
      ┌─────┴─────┐
      │ Codegen   │
      └─────┬─────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌─────────┐    ┌─────────┐
│ Python  │    │Frontend │
│ Models  │    │  Types  │
└────┬────┘    └────┬────┘
     │              │
     ▼              ▼
┌─────────┐    ┌─────────┐
│GraphQL  │    │  React  │
│ Server  │◄───│   App   │
└─────────┘    └─────────┘
```

## Key Benefits

1. **Single Source of Truth**: TypeScript models define the contract
2. **Type Safety**: Branded types and enums ensure consistency
3. **Automatic Synchronization**: Code generation keeps all layers in sync
4. **Language-Idiomatic**: Generated code follows Python/TypeScript conventions
5. **Validation**: Pydantic models provide runtime validation in Python
6. **GraphQL Integration**: Seamless type mapping between layers

## Development Workflow

1. Modify TypeScript models in `dipeo/models/src/`
2. Run `make codegen` or `pnpm codegen` which performs:
   - Domain model generation (TypeScript → Python)
   - GraphQL schema export from server
   - TypeScript type generation for frontend
   - GraphQL operations generation for CLI
3. Generated files are updated:
   - Python models
   - Python conversions
   - GraphQL schema (`make graphql-schema` can be run separately)
4. Frontend runs codegen to update GraphQL types
5. All layers now use the updated domain models

This architecture ensures that domain model changes propagate correctly through the entire stack while maintaining type safety and validation at each layer.

## New Domain Features

### Tool System

DiPeO now supports integrating external tools with LLM conversations:

**Available Tools**:
- **WEB_SEARCH**: Web search functionality for retrieving information
- **WEB_SEARCH_PREVIEW**: Web search with preview capabilities
- **IMAGE_GENERATION**: AI-powered image generation

Tools are configured through the `ToolConfig` interface and can be enabled for specific LLM requests.

### Hook System

Hooks provide extensibility points for custom processing:

**Hook Types**:
- **SHELL**: Execute shell commands
- **WEBHOOK**: Call external HTTP endpoints
- **PYTHON**: Run Python scripts
- **FILE**: File-based operations

**Trigger Modes**:
- **MANUAL**: Triggered explicitly by user action
- **HOOK**: Triggered automatically by system events

### Store Format Pattern

The frontend uses a "Store format" for efficient state management, converting between:
- **GraphQL format**: Arrays of nodes/arrows (for API communication)
- **Store format**: Maps indexed by ID (for O(1) lookups in UI)

This conversion is handled by `graphql-conversions.ts` and provides:
- Fast node/arrow lookups by ID
- Efficient updates and deletions
- Type-safe conversions between formats

### Additional Services

Beyond the core LLM providers (OpenAI, Anthropic, Google, Grok), DiPeO now supports:

**LLM Services**:
- **DEEPSEEK**: DeepSeek AI models

**API Services**:
- **GOOGLE_SEARCH**: Google search integration
- **SLACK**: Slack messaging integration
- **GITHUB**: GitHub repository operations
- **JIRA**: Jira issue tracking
- **NOTION**: Notion workspace integration (existing but more integrated)

## Handles: DiPeO's Connection System

Handles are a special type in DiPeO that enable nodes to connect to each other through arrows. They represent the input and output ports of nodes in the visual programming environment.

### Handle Model Definition

The TypeScript domain model defines handles with:
```typescript
export interface DomainHandle {
  id: HandleID;          // Branded type for type safety
  node_id: NodeID;       // The node this handle belongs to
  label: string;         // Display name (e.g., "input", "output", "true", "false")
  direction: HandleDirection;  // INPUT or OUTPUT
  data_type: DataType;   // Type of data flowing through
  position?: string | null;  // Visual position: 'left' | 'right' | 'top' | 'bottom'
}
```

### Handle ID Format

Handles use a specific ID format for consistency across the system:
```
Format: [nodeId]_[handleLabel]_[direction]
Example: "node123_output_output"
```

Note: The handle ID format uses underscores as separators. The `nodeId` component may itself contain underscores, which is why the parsing functions work backward from the end of the string.

This format is created and parsed by utility functions:

**TypeScript** (`dipeo/models/src/conversions.ts`):
```typescript
export function createHandleId(
  nodeId: NodeID,
  handleLabel: HandleLabel,  // Note: HandleLabel enum type
  direction: HandleDirection
): HandleID {
  return `${nodeId}_${handleLabel}_${direction}` as HandleID;
}

export function parseHandleId(handleId: HandleID) {
  // Handles node IDs that may contain underscores by working backward
  const lastUnderscoreIdx = handleId.lastIndexOf('_');
  const secondLastUnderscoreIdx = handleId.lastIndexOf('_', lastUnderscoreIdx - 1);
  
  return {
    node_id: handleId.substring(0, secondLastUnderscoreIdx) as NodeID,
    handle_label: handleId.substring(secondLastUnderscoreIdx + 1, lastUnderscoreIdx),
    direction: HandleDirection[handleId.substring(lastUnderscoreIdx + 1).toUpperCase()]
  };
}
```

**Python** (implemented in `dipeo_domain/handle_utils.py`):
```python
def create_handle_id(
    node_id: NodeID,
    handle_label: HandleLabel,
    direction: HandleDirection
) -> HandleID:
    return HandleID(f"{node_id}_{handle_label.value}_{direction.value}")

def parse_handle_id(handle_id: HandleID) -> ParsedHandle:
    # Works backward to handle node IDs with underscores
    last_underscore_idx = handle_id.rfind('_')
    second_last_underscore_idx = handle_id.rfind('_', 0, last_underscore_idx)
    # Parsing logic extracts components
```

### Handle-Arrow Connection System

Arrows connect nodes by referencing handle IDs:
```typescript
export interface DomainArrow {
  id: ArrowID;
  source: HandleID;  // Must be an OUTPUT handle
  target: HandleID;  // Must be an INPUT handle
  content_type?: ContentType;
  label?: string;
  data?: Record<string, any>;
}
```

This ensures:
- Type-safe connections (arrows can only connect compatible handles)
- Clear data flow direction (output → input)
- Validation at connection time

### Handle Generation by Node Type

Different node types have different handle configurations, automatically generated:

| Node Type        | Input Handles   | Output Handles |
|------------------|-----------------|----------------|
| start            | None            | output         |
| endpoint         | input           | None           |
| condition        | input           | true, false    |
| person_job       | first, default  | default        |
| person_batch_job | default         | default        |
| code_job         | default         | default        |
| api_job          | default         | default        |
| db               | default         | default        |
| user_response    | default         | default        |
| hook             | default         | default        |

### Frontend Handle Implementation

The frontend uses handles with React Flow:

1. **Visual Representation** (`FlowHandle.tsx`):
   - Renders as labeled pills outside node boundaries
   - Color-coded: blue for inputs, green for outputs
   - Interactive hover states and connection validation

2. **Handle Registry**:
   - Frontend maintains a handle index for O(1) lookups
   - Maps handle IDs to their node and position data
   - Used for efficient connection validation

3. **Connection Validation**:
   ```typescript
   const isValidConnection = (source: HandleID, target: HandleID) => {
     const sourceHandle = handleRegistry[source];
     const targetHandle = handleRegistry[target];
     
     return sourceHandle.direction === 'OUTPUT' && 
            targetHandle.direction === 'INPUT' &&
            isDataTypeCompatible(sourceHandle.data_type, targetHandle.data_type);
   };
   ```

### Backend Handle Processing

1. **Automatic Generation** (`HandleGenerator`):
   - Generates handles based on node type during diagram conversion
   - Ensures consistency between diagram formats

2. **Validation**:
   - Validates handle existence when creating arrows
   - Checks direction compatibility (output → input only)
   - Verifies data type compatibility

3. **Execution Context**:
   - Handle connections determine execution flow
   - Data passes through handles during node execution
   - Handle labels used for accessing node inputs/outputs

### Handle System Benefits

1. **Type Safety**: Branded types prevent invalid handle references
2. **Visual Clarity**: Clear representation of data flow in diagrams
3. **Flexibility**: Nodes can have multiple inputs/outputs with different types
4. **Consistency**: Same handle ID format across TypeScript, Python, and GraphQL
5. **Performance**: Indexed lookups enable efficient connection validation
6. **Extensibility**: Easy to add new handle types or configurations

The handle system is fundamental to DiPeO's visual programming paradigm, providing a robust and type-safe way to connect nodes and define data flow through the diagram.