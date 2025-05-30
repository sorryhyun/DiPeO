
## 4. **Mixed API Base URL Handling**
Inconsistent patterns across files:

```typescript
// In TopBar.tsx
const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';

// In useDiagramRunner.ts
const STREAMING_API_BASE = import.meta.env.DEV 
  ? 'http://localhost:8000'  // Direct connection in dev
  : '';
```

## 5. **Tailwind CSS Static Safelist**
Your `tailwind.config.js` has a large hardcoded safelist:

```javascript
safelist: [
  'border-gray-400', 'ring-gray-300', 'bg-gray-500', 'shadow-gray-200',
  'border-blue-400', 'ring-blue-300', 'bg-blue-500', 'shadow-blue-200',
  // ... many more
]
```

**Issue**: This indicates dynamic class generation that should be refactored to use static classes or CSS-in-JS.

## 6. **Deprecated Block Type**
In `types.ts`:
```typescript
export type BlockType = 'start' | 'person_job' | 'db' | 'job' | 'condition' | 'endpoint' ; // db_target is deprecated
```

But no migration path is provided for `db_target`.

## 7. **Store CRUD Pattern Over-engineering**
You have generic CRUD utilities that create differently named methods:

```typescript
// In storeCrudUtils.ts
export function createPersonCrudActions<T extends CrudItem>(...)
export function createApiKeyCrudActions<T extends CrudItem>(...)
```

**Issue**: These could be consolidated into a single pattern with consistent naming.

## 8. **Error Handling Inconsistency**
Some places use the error factory pattern:
```typescript
const handleAsyncError = createAsyncErrorHandler(toast);
```

Others use toast directly:
```typescript
toast.error('Failed to load conversations');
```

## 9. **WebSocket vs SSE Mixed Usage**
- `useDiagramRunner.ts` uses SSE for streaming
- `useExecutionMonitor.ts` uses WebSocket

This suggests an incomplete migration between protocols.

## 10. **Component Wrapper Pattern**
Many components in the app wrap package components just to connect stores:

```typescript
// In Canvas.tsx
const CustomArrow = (props: any) => {
  const updateArrowData = useArrowDataUpdater();
  return <CustomArrowBase {...props} onUpdateData={updateArrowData} />;
};
```

## Recommendations:

4. **Create a central API configuration** - Single source of truth for API endpoints
5. **Refactor dynamic Tailwind classes** - Use data attributes or CSS modules
6. **Remove deprecated types** - Clean up `db_target` references
7. **Standardize store patterns** - One CRUD pattern for all entities
8. **Unify error handling** - Always use the factory pattern
9. **Choose WebSocket or SSE** - Don't mix both
10. **Consider a proper DI pattern** - Instead of wrapper components, use context or composition

The codebase shows signs of being in mid-migration. While the new patterns are good, the old ones haven't been fully removed, creating maintenance overhead and potential bugs.