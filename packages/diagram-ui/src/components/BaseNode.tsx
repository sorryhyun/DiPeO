import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { RotateCcw } from 'lucide-react';
import { Button } from '@repo/ui-kit';
import { BaseNodeProps, NodeConfig } from '@repo/core-model';
import { createHandleId } from '../utils/nodeHelpers';

function BaseNodeComponent({
  id,
  children,
  className = '',
  selected = false,
  onFlip,
  handles = [],
  borderColor = 'gray',
  showFlipButton = true,
  nodeType,
  data,
  autoHandles = false,
  isRunning = false,
  onUpdateData,
  onUpdateNodeInternals,
  nodeConfigs = {},
  ...divProps
}: BaseNodeProps) {
  
  // Check if node is flipped
  const isFlipped = data?.flipped === true;
  
  // Get configuration if nodeType is provided
  const config = nodeType ? nodeConfigs[nodeType] : null;
  
  // Use auto-generated handles if autoHandles is true and config exists
  const effectiveHandles = React.useMemo(() => {
    if (autoHandles && config) {
      return config.handles.map(handle => {
        const isVertical = handle.position === Position.Top || handle.position === Position.Bottom;
        const position = isFlipped && !isVertical
          ? (handle.position === Position.Left ? Position.Right : Position.Left)
          : handle.position;
        
        const style = isVertical 
          ? { left: `${handle.offset}%` }
          : { top: `${handle.offset}%` };
        
        return {
          type: handle.type,
          position,
          id: createHandleId(id, handle.type, handle.name),
          style,
          className: handle.color
        };
      });
    }
    return handles;
  }, [autoHandles, config, handles, id, isFlipped]);
  
  // Use config values if available and not overridden
  const effectiveBorderColor = (autoHandles && config?.borderColor) || borderColor;
  const effectiveClassName = `${(autoHandles && config?.width) || ''} ${(autoHandles && config?.className) || ''} ${className}`.trim();
  
  // Handle flip with update if using auto handles
  const handleFlip = React.useCallback(() => {
    if (autoHandles && onUpdateData && onUpdateNodeInternals) {
      onUpdateData(id, { flipped: !isFlipped });
      onUpdateNodeInternals(id);
    } else if (onFlip) {
      onFlip();
    }
  }, [autoHandles, id, isFlipped, onFlip, onUpdateData, onUpdateNodeInternals]);
  

  // Pre-defined color mappings for Tailwind CSS
  const colorMappings = {
    gray: { border: 'border-gray-400', ring: 'ring-gray-300', handle: 'bg-gray-500', shadow: 'shadow-gray-200' },
    blue: { border: 'border-blue-400', ring: 'ring-blue-300', handle: 'bg-blue-500', shadow: 'shadow-blue-200' },
    green: { border: 'border-green-400', ring: 'ring-green-300', handle: 'bg-green-500', shadow: 'shadow-green-200' },
    red: { border: 'border-red-400', ring: 'ring-red-300', handle: 'bg-red-500', shadow: 'shadow-red-200' },
    purple: { border: 'border-purple-400', ring: 'ring-purple-300', handle: 'bg-purple-500', shadow: 'shadow-purple-200' },
    yellow: { border: 'border-yellow-400', ring: 'ring-yellow-300', handle: 'bg-yellow-500', shadow: 'shadow-yellow-200' },
  };

  const colors = colorMappings[effectiveBorderColor as keyof typeof colorMappings] || colorMappings.gray;

  const borderClass = selected
    ? `${colors.border} ring-2 ${colors.ring}` // Removed: ${colors.shadow}
    : isRunning
    ? 'border-green-500 ring-4 ring-green-300 shadow-lg shadow-green-200 scale-105'
    : `border-gray-300`; // Removed: hover:${colors.border} hover:${colors.shadow} transition-all duration-200

  const finalClassName = `relative p-2 border-2 rounded-lg ${borderClass} ${effectiveClassName} ${isRunning ? 'animate-pulse bg-green-50' : 'bg-white'}`;
  

  return (
    <div
      {...divProps}
      className={finalClassName}
    >
      {/* Add multiple visual indicators for running state */}
      {isRunning && (
        <>
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-ping" />
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full" />
          <div className="absolute inset-0 bg-green-100 opacity-20 rounded-lg animate-pulse" />
        </>
      )}
      
      {/* Flip button */}
      {showFlipButton && selected && (onFlip || (autoHandles && onUpdateData && onUpdateNodeInternals)) && !isRunning && (
        <Button
          onClick={handleFlip}
          variant="outline"
          size="icon"
          className="absolute -top-3 left-1/2 transform -translate-x-1/2 w-6 h-6 rounded-full shadow-md bg-white hover:bg-gray-50 transition-colors duration-200"
          title="Flip handles"
        >
          <RotateCcw className="w-3 h-3" />
        </Button>
      )}

      {/* Content with running indicator */}
      <div className={isRunning ? 'relative z-10' : ''}>
        {children}
        {isRunning && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-green-500 animate-pulse rounded-b" />
        )}
      </div>

      {/* Handles */}
      {effectiveHandles.map((handle, index) => (
        <Handle
          key={handle.id || index}
          type={handle.type === 'input' ? 'target' : 'source'}
          position={handle.position}
          id={handle.id}
          style={{ 
            width: '16px',
            height: '16px',
            backgroundColor: handle.className?.includes('bg-green') ? '#16a34a' :
                           handle.className?.includes('bg-blue') ? '#2563eb' :
                           handle.className?.includes('bg-red') ? '#dc2626' :
                           handle.className?.includes('bg-purple') ? '#9333ea' :
                           handle.className?.includes('bg-teal') ? '#0d9488' :
                           handle.className?.includes('bg-orange') ? '#ea580c' :
                           handle.className?.includes('bg-indigo') ? '#4f46e5' :
                           handle.className?.includes('bg-amber') ? '#d97706' :
                           '#6b7280',
            border: '2px solid white',
            ...handle.style 
          }}
          className={`w-4 h-4 ${isRunning ? 'animate-pulse' : ''}`}
        />
      ))}
    </div>
  );
}

// Memoized BaseNode with custom comparison
export const BaseNode = React.memo(BaseNodeComponent, (prevProps, nextProps) => {
  // Only re-render if these specific props change
  return (
    prevProps.id === nextProps.id &&
    prevProps.selected === nextProps.selected &&
    prevProps.isRunning === nextProps.isRunning &&
    prevProps.data?.flipped === nextProps.data?.flipped &&
    prevProps.borderColor === nextProps.borderColor &&
    prevProps.showFlipButton === nextProps.showFlipButton &&
    prevProps.nodeType === nextProps.nodeType &&
    prevProps.autoHandles === nextProps.autoHandles &&
    // Deep compare handles array
    JSON.stringify(prevProps.handles) === JSON.stringify(nextProps.handles) &&
    // Compare children (if they're simple types)
    prevProps.children === nextProps.children
  );
});

BaseNode.displayName = 'BaseNode';