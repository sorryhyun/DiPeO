# Store Migration Guide

This guide explains how to migrate from the current unified store to the new slice-based architecture.

## What's New

### 1. Store Slices
The monolithic unified store has been split into focused slices:
- `diagramSlice` - Node and arrow management
- `executionSlice` - Execution state and node runtime states
- `personSlice` - LLM person management
- `uiSlice` - UI state (selection, modals, views)
- `computedSlice` - Computed getters for efficient data access

### 2. Focused Selector Hooks
Replace repetitive `useShallow` patterns with specialized hooks:
- `useDiagramData()` - Access nodes, arrows, and arrays
- `useExecutionData()` - Execution state with computed progress
- `useUIState()` - UI state with computed values
- `usePersonsData()` - Person data with usage statistics

### 3. Core Types
- Single source of truth in `types/core.ts`
- Fixed duplicate `NodeState` definitions
- Clear separation between domain and UI types

## Migration Steps

### Step 1: Update Store Import
```typescript
// Old
import { useUnifiedStore } from '@/stores/unifiedStore';

// New (once migrated)
import { useUnifiedStore } from '@/stores/unifiedStore.refactored';
```

### Step 2: Replace Direct Store Access
```typescript
// Old
const store = useUnifiedStore();
const nodes = store.nodes;
const arrows = store.arrows;

// New
import { useDiagramData } from '@/hooks/selectors';
const { nodes, arrows, nodesArray, arrowsArray } = useDiagramData();
```

### Step 3: Update Execution State Access
```typescript
// Old
const execution = useUnifiedStore(state => state.execution);
const isRunning = execution.isRunning;

// New
import { useExecutionData } from '@/hooks/selectors';
const { isRunning, progress, runningNodes } = useExecutionData();
```

### Step 4: Update UI State Access
```typescript
// Old
const selectedId = useUnifiedStore(state => state.selectedId);
const readOnly = useUnifiedStore(state => state.readOnly);

// New
import { useUIState } from '@/hooks/selectors';
const { selectedId, readOnly, hasSelection } = useUIState();
```

### Step 5: Update Type Imports
```typescript
// Old
import { NodeState } from '@/stores/unifiedStore.types';

// New
import { NodeExecutionState } from '@/types/core';
// or
import { NodeState } from '@/stores/slices/executionSlice';
```

## Benefits

1. **Performance**: Focused selectors reduce re-renders
2. **Type Safety**: Better TypeScript inference with slices
3. **Maintainability**: Clear separation of concerns
4. **Developer Experience**: Intuitive hooks with computed values

## Testing Strategy

1. Start with read-only operations (selectors)
2. Test each slice independently
3. Verify computed values match expectations
4. Check for any missing functionality

## Rollback Plan

The new architecture is in separate files, so rollback is simple:
1. Keep using the original `unifiedStore.ts`
2. Delete new files if needed
3. No data migration required

## Next Steps

Once testing is complete:
1. Replace `unifiedStore.ts` with `unifiedStore.refactored.ts`
2. Update all imports project-wide
3. Remove legacy selector patterns
4. Delete unused code