// packages/diagram-ui/src/components/FlowHandle.tsx
import React, { useMemo } from 'react';
import { Handle, Position, HandleProps } from '@xyflow/react';
import { createHandleId } from '@/utils/canvas/handle-adapter';

export interface FlowHandleProps extends Omit<HandleProps, 'type' | 'id'> {
  nodeId: string;
  type: 'input' | 'output';
  name: string;
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

// Pre-computed label position lookups
const LABEL_BASE_STYLE: React.CSSProperties = {
  position: 'absolute',
  fontSize: '10px',
  fontWeight: 500,
  color: '#666',
  whiteSpace: 'nowrap',
  pointerEvents: 'none',
  userSelect: 'none',
};

const LABEL_POS = {
  [Position.Top]: {
    ...LABEL_BASE_STYLE,
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  [Position.Bottom]: {
    ...LABEL_BASE_STYLE,
    top: '-20px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  [Position.Left]: {
    ...LABEL_BASE_STYLE,
    right: '20px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  [Position.Right]: {
    ...LABEL_BASE_STYLE,
    left: '20px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
} as const;

// Label position for handle relative positioning
const LABEL_HANDLE_POS = {
  [Position.Top]: { top: `-${HALF_HANDLE_SIZE}px` },
  [Position.Bottom]: { bottom: `-${HALF_HANDLE_SIZE}px` },
  [Position.Left]: { left: `-${HALF_HANDLE_SIZE}px` },
  [Position.Right]: { right: `-${HALF_HANDLE_SIZE}px` },
} as const;

const FlowHandleComponent: React.FC<FlowHandleProps> = ({
  nodeId,
  type,
  name,
  position,
  offset = 50,
  color,
  className,
  ...props
}) => {
  const rfType = type === 'output' ? 'source' : 'target';
  const handleId = createHandleId(nodeId, name);

  // Memoize computed styles
  const handleStyle = useMemo(() => {
    const baseColor = color || (type === 'output' ? '#16a34a' : '#2563eb');
    return {
      width: '16px',
      height: '16px',
      backgroundColor: baseColor,
      border: '2px solid white',
      ...HANDLE_POS[position](offset),
      position: 'absolute' as const,
    };
  }, [position, offset, color, type]);

  // Memoize label style computation
  const labelStyle = useMemo(() => {
    // Regular handles
    return {
      ...LABEL_POS[position],
      position: 'absolute' as const,
      zIndex: 10,
      ...LABEL_HANDLE_POS[position],
    };
  }, [position]);

  return (
    <>
      <Handle
        type={rfType}
        position={position}
        id={handleId}
        style={handleStyle}
        className={className}
        {...props}
      />
      <span style={labelStyle}>{name}</span>
    </>
  );
};

// Memoized version with custom comparison
export const FlowHandle = React.memo(FlowHandleComponent, (prevProps, nextProps) => {
  // Compare only the props that affect rendering
  return (
    prevProps.nodeId === nextProps.nodeId &&
    prevProps.name === nextProps.name &&
    prevProps.type === nextProps.type &&
    prevProps.position === nextProps.position &&
    prevProps.offset === nextProps.offset &&
    prevProps.color === nextProps.color &&
    prevProps.className === nextProps.className
  );
});