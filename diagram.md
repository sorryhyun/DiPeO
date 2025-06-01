# Diagram Feature Removal Plan

## Current State Analysis
The `features/diagram/` directory serves as an unnecessary orchestration layer with minimal value:

```
features/diagram/
├── hooks/useDiagramActions.ts      # Just re-exports from serialization
├── utils/diagramHelpers.ts         # General utilities misplaced here  
├── components/ui-components/Arrow.tsx  # Duplicate of canvas/Arrow.tsx
└── hooks/ui-hooks/usePropertyForm.ts   # Belongs in properties feature
```

## Reorganization Plan

### 1. Move Core Utilities → Shared
**File**: `features/diagram/utils/diagramHelpers.ts`
**Target**: `shared/utils/diagramUtils.ts`
**Functions**: `validateDiagram`, `findPathsFromNode`, `getNodeDependencies`, `getDiagramStatistics`, `duplicateNode`

### 2. Eliminate Orchestration Wrapper
**File**: `features/diagram/hooks/useDiagramActions.ts`
**Action**: Delete entirely
**Replacement**: Direct imports from `features/serialization/hooks/`

### 3. Remove Duplicate Component
**File**: `features/diagram/components/ui-components/Arrow.tsx`
**Action**: Delete (use `features/canvas/components/ui-components/Arrow.tsx`)

### 4. Relocate Misplaced Hook
**File**: `features/diagram/hooks/ui-hooks/usePropertyForm.ts` 
**Target**: `features/properties/hooks/usePropertyForm.ts`

### 5. Update Import References
Replace all `@/features/diagram/hooks/useDiagramActions` imports with direct serialization imports:
```typescript
// Before
import { useDiagramActions } from '@/features/diagram/hooks/useDiagramActions';
const { onExportYAML } = useDiagramActions();

// After  
import { useExport } from '@/features/serialization/hooks/useExport';
const { onExportYAML } = useExport();
```

### 6. Delete Directory
**Action**: Remove entire `features/diagram/` directory
**Coordination**: Handled by existing features:
- **Execution**: `features/execution/hooks/useDiagramRunner`
- **Serialization**: `features/serialization/hooks/useExport, useFileImport`
- **Canvas**: `features/canvas/hooks/useCanvasActions`

## Benefits
- **Eliminates unnecessary abstraction layer**
- **Moves utilities to proper shared location**
- **Removes code duplication**
- **Cleaner, more direct imports**
- **Better alignment with feature-based architecture**

## Implementation Order
1. Move `diagramHelpers.ts` → `shared/utils/diagramUtils.ts`
2. Move `usePropertyForm.ts` → `properties/hooks/`
3. Update all import references across codebase
4. Delete `features/diagram/` directory
5. Update feature exports and documentation