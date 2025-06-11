import React from 'react';
import { BaseNode } from './nodes/BaseNode';
import { NodeKind } from '@/types';

interface DragPreviewProps {
  position: { x: number; y: number };
  nodeType?: NodeKind;
  isDraggingNode: boolean;
  opacity?: number;
}

export const DragPreview: React.FC<DragPreviewProps> = ({ 
  position, 
  nodeType, 
  isDraggingNode,
  opacity = 0.5 
}) => {
  if (!isDraggingNode || !nodeType) return null;

  return (
    <div
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        pointerEvents: 'none',
        opacity,
        transform: 'translate(-50%, -50%)',
        zIndex: 9999,
        // Add a subtle shadow to make it more visible
        filter: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))',
      }}
    >
      <div style={{ transform: 'scale(0.8)' }}>
        <BaseNode
          id="preview"
          type={nodeType}
          data={{
            label: nodeType.charAt(0).toUpperCase() + nodeType.slice(1).replace(/_/g, ' ')
          }}
          selected={false}
        />
      </div>
    </div>
  );
};