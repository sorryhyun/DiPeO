// packages/diagram-ui/src/components/FlowHandle.tsx
import React, { useMemo } from 'react';
import { Handle, Position, HandleProps } from '@xyflow/react';
import type { NodeID } from '@dipeo/domain-models';

export interface FlowHandleProps extends Omit<HandleProps, 'type' | 'id'> {
  nodeId: NodeID;
  type: 'input' | 'output';
  label: string;
  position: Position;
  offset?: number;
  color?: string;
  className?: string;
  nodeType?: string;
}

// Pre-computed constants
const HANDLE_SIZE = 16;
const HALF_HANDLE_SIZE = HANDLE_SIZE / 2;
const HANDLE_DISTANCE = 30; // Increased distance from node edge

// Pre-computed position lookups
const HANDLE_POS = {
  [Position.Top]: (offset: number) => ({
    left: `${offset}%`,
    top: `-${HANDLE_DISTANCE}px`,
    transform: 'translateX(-50%)'
  }),
  [Position.Bottom]: (offset: number) => ({
    left: `${offset}%`,
    bottom: `-${HANDLE_DISTANCE}px`,
    transform: 'translateX(-50%)'
  }),
  [Position.Left]: (offset: number) => ({
    top: `${offset}%`,
    left: `-${HANDLE_DISTANCE}px`,
    transform: 'translateY(-50%)'
  }),
  [Position.Right]: (offset: number) => ({
    top: `${offset}%`,
    right: `-${HANDLE_DISTANCE}px`,
    transform: 'translateY(-50%)'
  })
} as const;

const FlowHandleComponent: React.FC<FlowHandleProps> = ({
  nodeId: _nodeId,
  type,
  label,
  position,
  offset = 50,
  color,
  className,
  nodeType,
  ...props
}) => {
  const rfType = type === 'output' ? 'source' : 'target';

  // Memoize computed styles for integrated pill-shaped handle
  const handleStyle = useMemo(() => {
    const baseColor = color || (type === 'output' ? '#16a34a' : '#2563eb');
    // Use smaller distance for start/endpoint nodes
    const isSmallNode = nodeType === 'start' || nodeType === 'endpoint';
    const distance = isSmallNode ? 20 : HANDLE_DISTANCE;
    
    return {
      width: 'auto',
      minWidth: '50px',
      height: '20px',
      backgroundColor: type === 'output' 
        ? 'rgba(34, 197, 94, 0.9)' 
        : 'rgba(59, 130, 246, 0.9)',
      border: `2px solid ${baseColor}`,
      borderRadius: '12px',
      padding: '0 8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '11px',
      fontWeight: 600,
      color: 'white',
      cursor: 'pointer',
      ...(() => {
        // Custom position calculation using dynamic distance
        switch (position) {
          case Position.Top:
            return {
              left: `${offset}%`,
              top: `-${distance}px`,
              transform: 'translateX(-50%)'
            };
          case Position.Bottom:
            return {
              left: `${offset}%`,
              bottom: `-${distance}px`,
              transform: 'translateX(-50%)'
            };
          case Position.Left:
            return {
              top: `${offset}%`,
              left: `-${distance}px`,
              transform: 'translateY(-50%)'
            };
          case Position.Right:
            return {
              top: `${offset}%`,
              right: `-${distance}px`,
              transform: 'translateY(-50%)'
            };
        }
      })(),
      position: 'absolute' as const,
    };
  }, [position, offset, color, type, nodeType]);

  return (
    <Handle
      type={rfType}
      position={position}
      id={label}
      style={handleStyle}
      className={className}
      {...props}
    >
      {label}
    </Handle>
  );
};

// Memoized version with custom comparison
export const FlowHandle = React.memo(FlowHandleComponent, (prevProps, nextProps) => {
  // Compare only the props that affect rendering
  return (
    prevProps.nodeId === nextProps.nodeId &&
    prevProps.label === nextProps.label &&
    prevProps.type === nextProps.type &&
    prevProps.position === nextProps.position &&
    prevProps.offset === nextProps.offset &&
    prevProps.color === nextProps.color &&
    prevProps.className === nextProps.className &&
    prevProps.nodeType === nextProps.nodeType
  );
});