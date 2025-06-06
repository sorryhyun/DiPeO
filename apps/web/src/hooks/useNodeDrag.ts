import { useCallback, useRef, type DragEvent } from 'react';
import { Node } from '@/common/types/core';

export const useNodeDrag = () => {
  // Store drag offset to align node properly with cursor
  const dragOffset = useRef({ x: 0, y: 0 });

  // Handle drag start for node types from sidebar
  const onDragStart = useCallback((event: DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    
    // Calculate offset from element center
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    dragOffset.current = {
      x: event.clientX - (rect.left + rect.width / 2),
      y: event.clientY - (rect.top + rect.height / 2)
    };
  }, []);

  // Handle drag over for canvas drop zone
  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop for adding nodes to canvas
  const onDrop = useCallback((
    event: DragEvent, 
    addNode: (type: Node['type'], position: { x: number; y: number }) => void,
    projectPosition: (x: number, y: number) => { x: number; y: number }
  ) => {
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;
    
    // Get the drop position - this should be where the cursor is
    const dropPosition = projectPosition(event.clientX, event.clientY);
    
    // Add the node at the drop position
    // React Flow will use this as the top-left corner of the node
    addNode(type as Node['type'], dropPosition);
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