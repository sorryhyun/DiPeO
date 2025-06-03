import { useCallback, type DragEvent } from 'react';

export const useNodeDrag = () => {
  // Handle drag start for node types from sidebar
  const onDragStart = useCallback((event: DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  // Handle drag over for canvas drop zone
  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop for adding nodes to canvas
  const onDrop = useCallback((
    event: DragEvent, 
    addNode: (type: string, position: { x: number; y: number }) => void,
    projectPosition: (x: number, y: number) => { x: number; y: number }
  ) => {
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;
    
    const position = projectPosition(event.clientX, event.clientY);
    addNode(type, position);
  }, []);

  // Handle drag over for person drop on nodes
  const onPersonDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
  }, []);

  // Handle person drop on nodes (for PersonJob nodes)
  const onPersonDrop = useCallback((
    event: DragEvent,
    nodeId: string,
    updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  ) => {
    const personId = event.dataTransfer.getData('application/person');
    if (personId) {
      updateNodeData(nodeId, { personId });
    }
  }, []);

  return {
    onDragStart,
    onDragOver,
    onDrop,
    onPersonDragOver,
    onPersonDrop
  };
};