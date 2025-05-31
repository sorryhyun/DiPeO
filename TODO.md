Let me trace through the wrapper overhead problem with a concrete example from your codebase:

## The BaseNode Wrapper Chain

Here's how a simple node component goes through **3 layers of wrapping**:

### Layer 1: Original BaseNode Component
```typescript
// apps/web/src/features/diagram/components/ui-components/BaseNode.tsx
function BaseNodeComponent({
  id, children, selected, isRunning, ...props
}: BaseNodeProps) {
  // 113 lines of actual implementation
  return <div>{children}</div>
}
```

### Layer 2: First Wrapper
```typescript
// apps/web/src/features/diagram/wrappers/index.ts
export { BaseNode } from '../components/ui-components/BaseNode';
// Just re-exports, but creates import indirection
```

### Layer 3: Store Integration Wrapper
```typescript
// apps/web/src/features/nodes/components/BaseNode.tsx
export const BaseNode = React.memo((props) => {
  const { id } = props;
  
  // Gets data from stores
  const { isRunning } = useNodeExecutionState(id);
  const { updateNodeData, updateNodeInternals, nodeConfigs } = useDiagramContext();
  
  // Passes everything to the actual BaseNode
  return (
    <BaseNodeComponent
      {...props}
      isRunning={isRunning}
      onUpdateData={updateNodeData}
      onUpdateNodeInternals={updateNodeInternals}
      nodeConfigs={nodeConfigs}
    />
  );
});
```

### Layer 4: Usage in Actual Nodes
```typescript
// apps/web/src/features/nodes/components/nodes/StartNode.tsx
const StartNode = ({ id, data, selected }) => {
  return (
    <GenericNode id={id} data={data} selected={selected}>
      {/* content */}
    </GenericNode>
  );
};

// GenericNode also wraps BaseNode!
```

## Why This Is Inefficient

1. **Props Drilling**: Every prop must pass through 3-4 components
2. **Bundle Size**: Each wrapper adds ~20-50 lines of code
3. **Runtime Overhead**: Extra function calls and React reconciliation
4. **Debugging Complexity**: Stack traces become harder to follow

## The Same Pattern Repeats

```typescript
// CustomArrow has similar wrapping:
CustomArrow (ui) → CustomArrowWrapper → CustomArrowWithStore

// ContextMenu:
ContextMenu (ui) → ContextMenuWrapper → ContextMenuWithDiagram

// Properties panels:
Panel → PanelWrapper → UniversalPropertiesPanel → PropertyRenderer
```

## What Should Have Been Done

Instead of wrapping, inject dependencies directly:

```typescript
// Single component with optional store integration
export const BaseNode = ({ id, children, ...props }) => {
  // Hooks are optional - component works without them
  const isRunning = useNodeExecutionState?.(id) ?? props.isRunning;
  const updateNodeData = useNodeDataUpdater?.() ?? props.onUpdateData;
  
  // Single implementation
  return <div className={isRunning ? 'running' : ''}>{children}</div>
};
```

Or use a provider pattern:

```typescript
// Provide dependencies once at the top
<DiagramProvider>
  <BaseNode id="123" /> {/* Gets deps from context */}
</DiagramProvider>

// For testing/isolation
<BaseNode id="123" isRunning={true} /> {/* Works without provider */}
```

## Impact on Your Bundle

Looking at your code:
- ~15 wrapper components
- Each adds 30-100 lines
- **Total overhead: ~1000-1500 lines of wrapper code**
- Plus increased complexity and harder tree-shaking

This wrapper pattern is why your "refactored" code is larger - you've added layers instead of simplifying the architecture.