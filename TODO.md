
## 7. **Store CRUD Pattern Over-engineering**
You have generic CRUD utilities that create differently named methods:

```typescript
// In storeCrudUtils.ts
export function createPersonCrudActions<T extends CrudItem>(...)
export function createApiKeyCrudActions<T extends CrudItem>(...)
```

**Issue**: These could be consolidated into a single pattern with consistent naming.

## **WebSocket vs SSE Mixed Usage**
- `useDiagramRunner.ts` uses SSE for streaming
- `useExecutionMonitor.ts` uses WebSocket

This suggests an incomplete migration between protocols.

## **Component Wrapper Pattern**
Many components in the app wrap package components just to connect stores:

```typescript
// In Canvas.tsx
const CustomArrow = (props: any) => {
  const updateArrowData = useArrowDataUpdater();
  return <CustomArrowBase {...props} onUpdateData={updateArrowData} />;
};
```

## Recommendations:

1. **Choose WebSocket or SSE** - Don't mix both
2. **Standardize store patterns** - One CRUD pattern for all entities
3. **Consider a proper DI pattern** - Instead of wrapper components, use context or composition

The codebase shows signs of being in mid-migration. While the new patterns are good, the old ones haven't been fully removed, creating maintenance overhead and potential bugs.