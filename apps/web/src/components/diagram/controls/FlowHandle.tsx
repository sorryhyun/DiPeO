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

  // Position handles exactly on the edge of the node
  const handleSize = 16; // Handle width/height
  const halfHandleSize = handleSize / 2;
  
  const getEdgePositionStyle = (): React.CSSProperties => {
    switch (position) {
      case Position.Top:
        return { 
          left: `${offset}%`, 
          top: `-${halfHandleSize}px`,
          transform: 'translateX(-50%)'
        };
      case Position.Bottom:
        return { 
          left: `${offset}%`, 
          bottom: `-${halfHandleSize}px`,
          transform: 'translateX(-50%)'
        };
      case Position.Left:
        return { 
          top: `${offset}%`, 
          left: `-${halfHandleSize}px`,
          transform: 'translateY(-50%)'
        };
      case Position.Right:
        return { 
          top: `${offset}%`, 
          right: `-${halfHandleSize}px`,
          transform: 'translateY(-50%)'
        };
      default:
        return positionStyle;
    }
  };

  const finalStyle: React.CSSProperties = {
    width: '16px',
    height: '16px',
    backgroundColor: color || (type === 'output' ? '#16a34a' : '#2563eb'),
    border: '2px solid white',
    ...getEdgePositionStyle(),
    ...style,
    // Override React Flow's default positioning
    position: 'absolute',
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
    <>
      <Handle
        type={rfType}
        position={position}
        id={handleId}
        style={finalStyle}
        className={className}
        {...props}
      />
      <span style={{
        ...getLabelStyle(),
        position: 'absolute',
        zIndex: 10,
        // Position label relative to handle position
        ...(position === Position.Top ? { top: `-${halfHandleSize}px` } : {}),
        ...(position === Position.Bottom ? { bottom: `-${halfHandleSize}px` } : {}),
        ...(position === Position.Left ? { left: `-${halfHandleSize}px` } : {}),
        ...(position === Position.Right ? { right: `-${halfHandleSize}px` } : {}),
      }}>{name}</span>
    </>
  );
};