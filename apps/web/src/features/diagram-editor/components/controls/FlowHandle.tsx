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
}

// Pre-computed constants
const HANDLE_SIZE = 16;
const HALF_HANDLE_SIZE = HANDLE_SIZE / 2;

// Pre-computed position lookups
const HANDLE_POS = {
  [Position.Top]: (offset: number) => ({
    left: `${offset}%`,
    top: `-${HALF_HANDLE_SIZE}px`,
    transform: 'translateX(-50%)'
  }),
  [Position.Bottom]: (offset: number) => ({
    left: `${offset}%`,
    bottom: `-${HALF_HANDLE_SIZE}px`,
    transform: 'translateX(-50%)'
  }),
  [Position.Left]: (offset: number) => ({
    top: `${offset}%`,
    left: `-${HALF_HANDLE_SIZE}px`,
    transform: 'translateY(-50%)'
  }),
  [Position.Right]: (offset: number) => ({
    top: `${offset}%`,
    right: `-${HALF_HANDLE_SIZE}px`,
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
  ...props
}) => {
  const rfType = type === 'output' ? 'source' : 'target';

  // Memoize computed styles for integrated pill-shaped handle
  const handleStyle = useMemo(() => {
    const baseColor = color || (type === 'output' ? '#16a34a' : '#2563eb');
    return {
      width: 'auto',
      minWidth: '60px',
      height: '24px',
      backgroundColor: type === 'output' 
        ? 'rgba(34, 197, 94, 0.9)' 
        : 'rgba(59, 130, 246, 0.9)',
      border: `2px solid ${baseColor}`,
      borderRadius: '12px',
      padding: '0 10px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '12px',
      fontWeight: 600,
      color: 'white',
      cursor: 'pointer',
      ...HANDLE_POS[position](offset),
      position: 'absolute' as const,
    };
  }, [position, offset, color, type]);

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
    prevProps.className === nextProps.className
  );
});