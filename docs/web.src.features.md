# Frontend Features Development Guide

## Feature Architecture

Each feature in `/features` follows a consistent module structure:

```
feature-name/
├── components/       # React components
├── hooks/           # Custom hooks
├── store/           # Zustand store slices
├── types/           # TypeScript types
├── utils/           # Feature-specific utilities
└── index.ts         # Public API exports
```

## Key Conventions

### 1. Component Organization
```typescript
// components/index.ts - Export all public components
export * from './MyComponent';
export { default as MyComponent } from './MyComponent';

// Lazy load heavy components
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));
```

### 2. Hook Patterns
```typescript
// hooks/useFeatureOperations.ts
export const useFeatureOperations = () => {
  const store = useUnifiedStore();
  const operations = useCanvasOperations();
  
  // Return stable references using useCallback/useMemo
  return useMemo(() => ({
    addItem: (data) => store.addItem(data),
    updateItem: (id, updates) => store.updateItem(id, updates)
  }), [store]);
};
```

### 3. Store Integration
```typescript
// store/featureSlice.ts
export const createFeatureSlice: StateCreator<UnifiedStore> = (set, get) => ({
  // State
  items: new Map(),
  
  // Actions with immer
  addItem: (item) => set(state => {
    state.items.set(item.id, item);
    state.dataVersion += 1;
  })
});
```

### 4. Type Definitions
```typescript
// types/index.ts
export interface FeatureState {
  items: Map<ItemID, Item>;
  selectedId: ItemID | null;
}
```

## Common Patterns

### Selector Hooks
```typescript
// Use focused selectors for performance
export const useFeatureData = () => {
  return useUnifiedStore(
    useShallow(state => ({
      items: state.items,
      itemsArray: Array.from(state.items.values())
    }))
  );
};
```

### Property Management
```typescript
// Use property manager for form state
const { formData, updateField, save } = usePropertyManager(
  entityId,
  'node',
  initialData,
  { autoSave: true, autoSaveDelay: 500 }
);
```

### GraphQL Integration
```typescript
// Use generated GraphQL hooks
const { data, loading } = useGetItemsQuery();
const [createItem] = useCreateItemMutation({
  onCompleted: (data) => toast.success('Created!'),
  refetchQueries: [GetItemsDocument]
});
```

## Adding New Features

1. Create feature directory structure
2. Define types in `types/index.ts`
3. Create store slice if needed
4. Build components with proper exports
5. Add hooks for operations
6. Export public API in feature's `index.ts`

## Important Dependencies

- **Store**: `useUnifiedStore` - Central state management
- **Canvas**: `useCanvasOperations` - Diagram operations
- **Execution**: `useExecution` - Runtime state
- **UI**: `@/shared/components/ui` - Shared components
- **GraphQL**: `@/__generated__/graphql` - Generated types/hooks

## Performance Tips

1. Use `React.memo` for expensive components
2. Implement `useShallow` for store selections
3. Debounce/throttle expensive operations
4. Lazy load heavy components
5. Cache computed values with `useMemo`