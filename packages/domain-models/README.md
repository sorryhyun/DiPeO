# @dipeo/domain-models

Shared domain models for DiPeO project. This package contains TypeScript interfaces and types that serve as the single source of truth for both frontend and backend.

## Overview

This package defines the core domain models used throughout the DiPeO system:

- **Diagram Domain**: Nodes, arrows, handles, persons, API keys, and diagram metadata
- **Execution Domain**: Execution states, events, results, and token usage tracking
- **Person Domain**: LLM agent configurations and conversation management

## Structure

```
src/
├── diagram/      # Diagram-related models (nodes, arrows, handles)
├── execution/    # Execution and runtime models
├── person/       # Person (LLM agent) models
└── index.ts      # Main entry point
```

## Key Features

- **TypeScript-first**: All models are defined as TypeScript interfaces
- **Validation**: Zod schemas provided for runtime validation
- **Type safety**: Branded types for IDs to prevent mixing different ID types
- **Utility functions**: Helper functions for common operations
- **Type guards**: Runtime type checking functions

## Usage

```typescript
import { 
  DomainNode, 
  DomainArrow, 
  ExecutionState,
  createEmptyDiagram,
  isDomainNode 
} from '@dipeo/domain-models';

// Create a new diagram
const diagram = createEmptyDiagram();

// Use type guards
if (isDomainNode(someObject)) {
  // TypeScript knows this is a DomainNode
  console.log(someObject.type);
}

// Use branded types for type safety
const nodeId: NodeID = 'node-123' as NodeID;
const arrowId: ArrowID = 'arrow-456' as ArrowID;
// This would be a compile error:
// const wrongId: NodeID = arrowId;
```

## Code Generation

These models can be used to generate Python Pydantic models for the backend:

```bash
# Example: Generate Python models from TypeScript
pnpm run generate:python
```

## Development

```bash
# Install dependencies
pnpm install

# Build the package
pnpm run build

# Run type checking
pnpm run typecheck

# Watch mode for development
pnpm run dev
```

## Conventions

1. **Naming**: Use `Domain` prefix for core domain models (e.g., `DomainNode`)
2. **IDs**: Use branded types for all IDs (e.g., `NodeID`, `ArrowID`)
3. **Timestamps**: Store as ISO datetime strings
4. **Optionals**: Use `null` for missing values, not `undefined`
5. **Enums**: Define as TypeScript enums for better type safety

## Migration Guide

When migrating from inline types to this package:

1. Replace local type definitions with imports from `@dipeo/domain-models`
2. Update ID types to use branded types
3. Use provided utility functions instead of custom implementations
4. Replace custom type guards with provided ones

Example:
```typescript
// Before
interface Node {
  id: string;
  type: string;
  // ...
}

// After
import { DomainNode, NodeID, NodeType } from '@dipeo/domain-models';
```