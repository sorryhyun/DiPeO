# DiagramAdapter Usage Guide

The `DiagramAdapter` provides centralized conversion between domain models and React Flow formats with performance optimization through caching.

## Basic Usage

```typescript
import { DiagramAdapter } from '@/adapters';
import { useDiagramData } from '@/hooks/selectors';

// Convert entire diagram to React Flow format
const { nodes, arrows } = useDiagramData();
const diagram = { nodes, arrows, handles, persons };
const { nodes: rfNodes, edges: rfEdges } = DiagramAdapter.toReactFlow(diagram);

// Convert individual elements
const rfNode = DiagramAdapter.nodeToReactFlow(domainNode, handles);
const rfEdge = DiagramAdapter.arrowToReactFlow(domainArrow);

// Convert back from React Flow
const domainNode = DiagramAdapter.reactToNode(rfNode);
const domainArrow = DiagramAdapter.reactToArrow(rfEdge);

// Validate connections
const validated = DiagramAdapter.validateConnection(connection, diagram);
if (validated.isValid) {
  const arrow = DiagramAdapter.connectionToArrow(connection);
}
```

## Performance Features

1. **WeakMap Caching**: Automatic caching of conversions for repeated access
2. **Immutable Conversions**: Position objects are cloned to prevent mutations
3. **Efficient Handle Mapping**: O(n) handle organization into input/output maps
4. **Lazy Evaluation**: Caches are populated on-demand

## Integration with Store

```typescript
// In a React component
function DiagramView() {
  const diagram = useDiagramData();
  const { nodes, edges } = useMemo(
    () => DiagramAdapter.toReactFlow(diagram),
    [diagram.dataVersion] // Only recompute when data changes
  );
  
  return <ReactFlow nodes={nodes} edges={edges} />;
}
```

## Memory Management

```typescript
// Clear caches when needed (e.g., on diagram switch)
useEffect(() => {
  return () => {
    DiagramAdapter.clearCaches();
  };
}, [diagramId]);
```

## Validation Features

The adapter includes comprehensive connection validation:
- Source/target existence checks
- Self-connection prevention
- Handle compatibility verification
- Duplicate connection detection
- Type-safe error messages