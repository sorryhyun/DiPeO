// packages/diagram-ui/src/components/FlowHandle.tsx
import React from 'react';
import { Handle, Position, HandleProps } from '@xyflow/react';
import { createHandleId } from '@/utils/node';

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

  // Determine label position based on handle position and type
  const getLabelStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      position: 'absolute',
      fontSize: '10px',
      fontWeight: 500,
      color: '#666',
      whiteSpace: 'nowrap',
      pointerEvents: 'none',
      userSelect: 'none',
    };

    // For DB nodes (bottom position with offset), show labels on sides
    if (position === Position.Bottom && style?.left) {
      const leftValue = parseFloat(String(style.left));
      if (leftValue < 0) {
        // Left side handle
        return {
          ...baseStyle,
          left: '-40px',
          top: '50%',
          transform: 'translateY(-50%)',
        };
      } else {
        // Right side handle
        return {
          ...baseStyle,
          right: '-40px',
          top: '50%',
          transform: 'translateY(-50%)',
        };
      }
    }

    // For regular handles, show above
    switch (position) {
      case Position.Top:
        return {
          ...baseStyle,
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
        };
      case Position.Bottom:
        return {
          ...baseStyle,
          top: '-20px',
          left: '50%',
          transform: 'translateX(-50%)',
        };
      case Position.Left:
        return {
          ...baseStyle,
          right: '20px',
          top: '50%',
          transform: 'translateY(-50%)',
        };
      case Position.Right:
        return {
          ...baseStyle,
          left: '20px',
          top: '50%',
          transform: 'translateY(-50%)',
        };
      default:
        return baseStyle;
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <span style={getLabelStyle()}>{name}</span>
      <Handle
        type={rfType}
        position={position}
        id={handleId}
        style={finalStyle}
        className={className}
        {...props}
      />
    </div>
  );
};