# Canvas Context Migration Guide

This guide helps migrate components from prop drilling to using the new CanvasContext.

## Overview

The CanvasContext eliminates prop drilling for commonly used canvas state and operations. It provides:

- **UI State**: Selection, canvas mode, read-only status, view settings
- **Operations**: Selection handlers, canvas operations, diagram operations, execution operations

## Migration Examples

### Example 1: PropertiesRenderer

**Before:**
```tsx
interface PropertiesRendererProps {
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  nodes: Map<NodeID, DiPeoNode>;
  arrows: Map<ArrowID, DiPeoEdge>;
  persons: Map<PersonID, Person>;
}

export function PropertiesRenderer({
  selectedNodeId,
  selectedArrowId,
  selectedPersonId,
  nodes,
  arrows,
  persons
}: PropertiesRendererProps) {
  // Component logic
}
```

**After:**
```tsx
import { useCanvasSelection } from '@/contexts/CanvasContext';
import { useDiagramData } from '@/hooks/selectors/useDiagramData';
import { usePersonsData } from '@/hooks/selectors/usePersonsData';

export function PropertiesRenderer() {
  const { selectedNodeId, selectedArrowId, selectedPersonId } = useCanvasSelection();
  const { nodes, arrows } = useDiagramData();
  const { persons } = usePersonsData();
  
  // Component logic remains the same
}
```

### Example 2: ContextMenu

**Before:**
```tsx
interface ContextMenuProps {
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  containerRef: React.RefObject<HTMLElement>;
  onAddNode: (type: NodeType, position: Vec2) => void;
  onAddPerson: (position: Vec2) => void;
  onDeleteNode: (nodeId: NodeID) => void;
  onDeleteArrow: (arrowId: ArrowID) => void;
  onClose: () => void;
  projectPosition: (pos: Vec2) => Vec2;
}
```

**After:**
```tsx
import { useCanvasContext } from '@/contexts/CanvasContext';

interface ContextMenuProps {
  containerRef: React.RefObject<HTMLElement>;
  onClose: () => void;
}

export function ContextMenu({ containerRef, onClose }: ContextMenuProps) {
  const { 
    selectedNodeId, 
    selectedArrowId,
    canvasOps: { projectPosition },
    diagramOps: { addNode, addPerson, deleteNode, deleteArrow }
  } = useCanvasContext();
  
  // Use operations directly
  const handleAddNode = (type: NodeType, position: Vec2) => {
    addNode({ type, position: projectPosition(position) });
  };
}
```

### Example 3: Component Using Read-Only State

**Before:**
```tsx
interface MyComponentProps {
  readOnly: boolean;
  isExecuting: boolean;
}

function MyComponent({ readOnly, isExecuting }: MyComponentProps) {
  const canEdit = !readOnly && !isExecuting;
  // ...
}
```

**After:**
```tsx
import { useCanvasReadOnly } from '@/contexts/CanvasContext';

function MyComponent() {
  const isReadOnly = useCanvasReadOnly();
  const canEdit = !isReadOnly;
  // ...
}
```

## Usage Patterns

### 1. Wrapping Your App

Add the CanvasProvider at a high level in your component tree:

```tsx
import { CanvasProvider } from '@/contexts/CanvasContext';

function App() {
  return (
    <CanvasProvider>
      <YourAppContent />
    </CanvasProvider>
  );
}
```

### 2. Choosing the Right Hook

- **`useCanvasContext()`**: Full access to all state and operations
- **`useCanvasUIState()`**: Only UI state (no operations)
- **`useCanvasSelection()`**: Only selection state and operations
- **`useCanvasReadOnly()`**: Simple boolean for edit permissions
- **`useCanvasOperations()`**: Only operations (no state)

### 3. Performance Considerations

The context uses `useShallow` from Zustand to prevent unnecessary re-renders. Components will only re-render when the specific values they use change.

## Migration Checklist

1. **Identify Props to Remove**
   - [ ] Selection state (`selectedNodeId`, `selectedArrowId`, etc.)
   - [ ] Canvas state (`readOnly`, `isExecuting`, `activeCanvas`)
   - [ ] View state (`zoom`, `position`)
   - [ ] Common operations (selection handlers, canvas operations)

2. **Update Component**
   - [ ] Remove props from interface
   - [ ] Import appropriate hook from CanvasContext
   - [ ] Replace prop usage with context values
   - [ ] Update parent components to stop passing removed props

3. **Test**
   - [ ] Verify component still works correctly
   - [ ] Check for performance issues
   - [ ] Ensure selection and operations work as expected

## Components to Migrate

Priority components for migration:

1. **High Priority** (Heavy prop drilling):
   - [ ] PropertiesRenderer
   - [ ] PropertiesTab
   - [ ] ContextMenu
   - [ ] Sidebar (right mode)
   - [ ] GenericPropertyPanel

2. **Medium Priority** (Moderate prop usage):
   - [ ] DiagramCanvas
   - [ ] NodeComponent variations
   - [ ] ArrowComponent
   - [ ] Toolbar components

3. **Low Priority** (Light prop usage):
   - [ ] Modal components
   - [ ] Settings panels
   - [ ] Utility components

## Benefits After Migration

1. **Cleaner Interfaces**: Components have fewer props
2. **Better Encapsulation**: Components fetch their own data
3. **Easier Refactoring**: Less coupling between parents and children
4. **Performance**: Only re-render when used values change
5. **Type Safety**: Strong typing throughout