# DiPeO Schema & Code Generation

## Overview
DiPeO uses automated code generation to maintain consistency between TypeScript (frontend) and Python (backend) domain models. This single-source-of-truth approach ensures type safety across the stack.

## Architecture

### Source Models (TypeScript)
```
packages/domain-models/src/
├── diagram.ts      # Core diagram types (nodes, arrows, persons)
├── execution.ts    # Execution state types
├── conversation.ts # Message/memory types
└── integration.ts  # External service types
```

### Generation Pipeline
```
TypeScript Models → Schema Extraction → Python Models
                                     ↘ Conversion Utils
```

## Key Scripts

### 1. Schema Extraction (`generate-schema.ts`)
- Parses TypeScript AST using ts-morph
- Extracts interfaces, enums, and type aliases
- Outputs `__generated__/schemas.json`

### 2. Python Generation (`generate-python.ts`)
- Converts TypeScript types to Python/Pydantic
- Handles branded types (e.g., `NodeID = NewType('NodeID', str)`)
- Maps TS types: `string→str`, `number→float/int`, arrays→`List[T]`
- Generates `dipeo_domain/models.py`

### 3. Conversion Utils (`generate-conversions.ts`)
- Generates helper functions for both TS and Python
- Node type mappings, handle ID parsing, validation rules
- Outputs to `dipeo_domain/conversions.py`

## Usage

### Generate All
```bash
cd packages/domain-models
pnpm generate:all
```

This runs:
1. `generate:schema` - Extract TypeScript schemas
2. `generate:python` - Generate Python models
3. `generate:conversions` - Generate utility functions

### In Python Code
```python
from dipeo_domain import (
    DomainNode,      # Auto-generated from diagram.ts
    NodeType,        # Enum with identical values
    ExecutionState,  # Consistent with frontend
)
```

## Type Consistency Examples

TypeScript:
```typescript
export type NodeID = string & { readonly __brand: 'NodeID' };
export enum NodeType { START = 'start', ... }
```

Generated Python:
```python
NodeID = NewType('NodeID', str)
class NodeType(str, Enum):
    start = "start"
```

## Benefits
- **Single source of truth**: Update TypeScript, Python follows automatically
- **Type safety**: Branded IDs prevent mixing NodeID/PersonID
- **Consistency**: Enums, field names, and structures match exactly
- **Maintainability**: No manual synchronization between frontend/backend