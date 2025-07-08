# Import Rules and Module Boundaries

This document defines the import rules and module boundaries for the DiPeO web application to maintain a clean, maintainable architecture.

## Module Hierarchy

The application follows a strict hierarchical structure:

```
@dipeo/domain-models (external package)
          ↓
      @lib/*
          ↓
      @core/*
          ↓
     @shared/*
          ↓
    @features/*
```

## Import Rules

### 1. **Domain Models** (`@dipeo/domain-models`)
- Can import: Nothing from the web app
- Can be imported by: All modules
- Purpose: Single source of truth for types and schemas

### 2. **Library** (`@lib/*`)
- Can import: 
  - `@dipeo/domain-models`
  - External npm packages
- Can be imported by: All modules
- Purpose: Non-feature utilities (GraphQL client, generic utils)
- Examples: `@lib/graphql`, `@lib/utils`

### 3. **Core** (`@core/*`)
- Can import:
  - `@dipeo/domain-models`
  - `@lib/*`
  - External npm packages
- Can be imported by: `@shared/*`, `@features/*`
- Purpose: Global application logic
- Contains:
  - Global store setup (`@core/store`)
  - Global providers (`@core/providers`)
  - Cross-cutting services (`@core/services`)
  - Core types (`@core/types`)

### 4. **Shared** (`@shared/*`)
- Can import:
  - `@dipeo/domain-models`
  - `@lib/*`
  - `@core/*` (sparingly, only for types and stores)
  - External npm packages
- Can be imported by: `@features/*`
- Purpose: Reusable UI components without business logic
- Contains:
  - Layout components (`@shared/components/layout`)
  - Form components (`@shared/components/forms`)
  - Feedback components (`@shared/components/feedback`)
  - Generic hooks (`@shared/hooks`)

### 5. **Features** (`@features/*`)
- Can import:
  - `@dipeo/domain-models`
  - `@lib/*`
  - `@core/*`
  - `@shared/*`
  - External npm packages
- Cannot import: Other features directly
- Purpose: Self-contained feature modules
- Each feature exports a public API via its index.ts

## ❌ Forbidden Import Patterns

1. **Features cannot import from other features directly**
   ```typescript
   // ❌ BAD
   import { DiagramCanvas } from '@features/diagram-editor/components/DiagramCanvas';
   
   // ✅ GOOD - Use the public API
   import { DiagramCanvas } from '@features/diagram-editor';
   ```

2. **Core/Shared cannot import from features**
   ```typescript
   // ❌ BAD - In a core or shared file
   import { ExecutionView } from '@features/execution-monitor';
   ```

3. **Library cannot import from any app modules**
   ```typescript
   // ❌ BAD - In a lib file
   import { useAppStore } from '@core/store';
   ```

## Inter-Feature Communication Patterns

Since features cannot directly import from each other, use these patterns:

### 1. **Through the Global Store**
Features communicate via the unified store:

```typescript
// In diagram-editor feature
const { setSelectedNode } = useAppStore();
setSelectedNode(nodeId);

// In properties-editor feature
const selectedNode = useAppStore(state => state.selectedNode);
```

### 2. **Through Events**
Use the browser's EventTarget API or a custom event bus:

```typescript
// In execution-monitor feature
window.dispatchEvent(new CustomEvent('execution:started', { 
  detail: { executionId } 
}));

// In diagram-editor feature
window.addEventListener('execution:started', (event) => {
  // Update UI based on execution
});
```

### 3. **Through Shared Services**
Place cross-cutting services in `@core/services`:

```typescript
// In @core/services/NotificationService.ts
export class NotificationService {
  notify(message: string) { /* ... */ }
}

// Used by any feature
import { NotificationService } from '@core/services';
```

### 4. **Through Props/Context**
Parent components can coordinate features:

```typescript
// In App.tsx or a page component
function WorkspacePage() {
  const [activeDiagram, setActiveDiagram] = useState();
  
  return (
    <>
      <DiagramEditor onDiagramChange={setActiveDiagram} />
      <PropertiesPanel diagram={activeDiagram} />
    </>
  );
}
```

## Enforcing Module Boundaries

### 1. **ESLint Rules**
Configure ESLint to enforce import restrictions:

```json
{
  "rules": {
    "no-restricted-imports": ["error", {
      "patterns": [
        {
          "group": ["@features/*/components/*", "@features/*/hooks/*"],
          "message": "Import from the feature's public API instead"
        }
      ]
    }]
  }
}
```

### 2. **TypeScript Project References**
Use TypeScript project references to enforce boundaries at compile time.

### 3. **Dependency Cruiser**
Use dependency-cruiser to visualize and validate the dependency graph.

## Best Practices

1. **Keep feature APIs minimal** - Only export what other parts of the app truly need
2. **Document public APIs** - Add JSDoc comments to exports in feature index files
3. **Use type-only imports** when possible to reduce runtime dependencies
4. **Prefer composition** over tight coupling between features
5. **Test boundaries** - Write tests that verify features work in isolation

## Example: Adding a New Feature

When adding a new feature:

1. Create the feature directory: `src/features/my-feature/`
2. Add standard subdirectories: `components/`, `hooks/`, `types/`, etc.
3. Create a public API in `index.ts`
4. Only import from allowed modules
5. Export only what's necessary for other features
6. Document the feature's public API

## Migration Guide

When refactoring existing code:

1. Identify cross-feature imports
2. Move shared logic to `@core` or `@shared`
3. Use communication patterns for feature coordination
4. Update imports to use public APIs
5. Add ESLint rules to prevent regression