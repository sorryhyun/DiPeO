// packages/diagram-ui/src/components/FlowHandle.tsx
import React from 'react';
import { Handle, Position, HandleProps } from '@xyflow/react';
import { createHandleId } from '@/common/utils/nodeHelpers';

export interface FlowHandleProps extends Omit<HandleProps, 'type' | 'id'> {
  nodeId: string;
  type: 'input' | 'output';
  name: string;
  position: Position;
  offset?: number;
  color?: string;
  style?: React.CSSProperties;
  className?: string;
}

export const FlowHandle: React.FC<FlowHandleProps> = ({
  nodeId,
  type,
  name,
  position,
  offset = 50,
  color,
  style,
  className,
  ...props
}) => {
  const rfType = type === 'output' ? 'source' : 'target';
  const handleId = createHandleId(nodeId, type, name);

  const isVertical = position === Position.Top || position === Position.Bottom;
  const positionStyle = isVertical
    ? { left: `${offset}%` }
    : { top: `${offset}%` };

  const finalStyle: React.CSSProperties = {
    width: '16px',
    height: '16px',
    backgroundColor: color || (type === 'output' ? '#16a34a' : '#2563eb'),
    border: '2px solid white',
    ...positionStyle,
    ...style,
  };

  return (
    <Handle
      type={rfType}
      position={position}
      id={handleId}
      style={finalStyle}
      className={className}
      {...props}
    />
  );
};