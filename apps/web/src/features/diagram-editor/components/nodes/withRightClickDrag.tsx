import React, { useCallback, useRef, useEffect } from 'react';
import { NodeProps, useReactFlow } from '@xyflow/react';
import { Vec2 } from '@dipeo/domain-models';

/**
 * Higher-order component that adds right-click drag functionality to nodes
 */
export function withRightClickDrag<P extends NodeProps>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return React.memo((props: P) => {
    const { getNode, setNodes } = useReactFlow();
    const isDragging = useRef(false);
    const startPosition = useRef<Vec2 | null>(null);
    const startMousePosition = useRef<Vec2 | null>(null);
    const nodeRef = useRef<HTMLDivElement>(null);

    const handleMouseDown = useCallback((event: React.MouseEvent) => {
      // Only handle right-click (button 2)
      if (event.button !== 2) return;
      
      event.preventDefault();
      event.stopPropagation();
      
      const node = getNode(props.id);
      if (!node) return;
      
      isDragging.current = true;
      startPosition.current = { x: node.position.x, y: node.position.y };
      startMousePosition.current = { x: event.clientX, y: event.clientY };
      
      // Prevent context menu during drag
      const preventContextMenu = (e: MouseEvent) => {
        if (isDragging.current) {
          e.preventDefault();
        }
      };
      
      // Add event listeners to window for drag
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('contextmenu', preventContextMenu);
      
      // Cleanup function
      const cleanup = () => {
        isDragging.current = false;
        startPosition.current = null;
        startMousePosition.current = null;
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
        window.removeEventListener('contextmenu', preventContextMenu);
      };
      
      // Store cleanup function
      (window as any).__rightClickDragCleanup = cleanup;
    }, [props.id, getNode]);

    const handleMouseMove = useCallback((event: MouseEvent) => {
      if (!isDragging.current || !startPosition.current || !startMousePosition.current) return;
      
      const deltaX = event.clientX - startMousePosition.current.x;
      const deltaY = event.clientY - startMousePosition.current.y;
      
      const newPosition = {
        x: startPosition.current.x + deltaX,
        y: startPosition.current.y + deltaY,
      };
      
      // Update node position
      setNodes((nodes) =>
        nodes.map((node) => {
          if (node.id === props.id) {
            return {
              ...node,
              position: newPosition,
            };
          }
          return node;
        })
      );
    }, [props.id, setNodes]);

    const handleMouseUp = useCallback((event: MouseEvent) => {
      if (event.button !== 2) return;
      
      // Call cleanup
      if ((window as any).__rightClickDragCleanup) {
        (window as any).__rightClickDragCleanup();
        delete (window as any).__rightClickDragCleanup;
      }
    }, []);

    // Cleanup on unmount
    useEffect(() => {
      return () => {
        if ((window as any).__rightClickDragCleanup) {
          (window as any).__rightClickDragCleanup();
          delete (window as any).__rightClickDragCleanup;
        }
      };
    }, []);

    return (
      <div 
        ref={nodeRef}
        onMouseDown={handleMouseDown}
        className="nodrag" // Prevent default ReactFlow drag
        style={{ width: '100%', height: '100%' }}
      >
        <Component {...props} />
      </div>
    );
  });
}

// Helper function to apply right-click drag to all node types
export function applyRightClickDragToNodeTypes<T extends Record<string, React.ComponentType<NodeProps>>>(
  nodeTypes: T
): T {
  const wrappedNodeTypes: any = {};
  
  for (const [key, Component] of Object.entries(nodeTypes)) {
    wrappedNodeTypes[key] = withRightClickDrag(Component);
  }
  
  return wrappedNodeTypes as T;
}