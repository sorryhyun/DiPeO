import React from 'react';
import { Position } from '@xyflow/react';
import { RotateCcw } from 'lucide-react';
import { Button } from '@/shared/components';
import { BaseNodeProps, HandleConfig } from '@/shared/types';
import { createHandleId } from '@/shared/utils/nodeHelpers';
import { FlowHandle } from './FlowHandle';
import { useNodeExecutionState } from '@/global/hooks/useStoreSelectors';
import { useDiagramContext } from '@/global/contexts/useDiagramContext';
import './BaseNode.css';

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
  isRunning: isRunningProp,
  onUpdateData: onUpdateDataProp,
  onUpdateNodeInternals: onUpdateNodeInternalsProp,
  nodeConfigs: nodeConfigsProp = {},
  ...divProps
}: BaseNodeProps) {
  
  // Always call hooks at the top level - React requires this
  const storeState = useNodeExecutionState(id);
  const storeContext = useDiagramContext();
  
  // Use store values or fallback to props
  const isRunning = storeState?.isRunning ?? isRunningProp ?? false;
  const onUpdateData = storeContext?.updateNodeData ?? onUpdateDataProp;
  const onUpdateNodeInternals = storeContext?.updateNodeInternals ?? onUpdateNodeInternalsProp;
  const nodeConfigs = storeContext?.nodeConfigs ?? nodeConfigsProp;
  
  // Check if node is flipped
  const isFlipped = data && typeof data === 'object' && 'flipped' in data && data.flipped === true;
  
  // Get configuration if nodeType is provided
  const config = nodeType ? nodeConfigs[nodeType] : null;
  
  // Use auto-generated handles if autoHandles is true and config exists
  const effectiveHandles = React.useMemo(() => {
    if (autoHandles && config) {
      return config.handles.map((handle: HandleConfig) => {
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
          name: handle.name,
          style,
          offset: handle.offset,
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
  

  // Apply base classes with data attributes for dynamic styling
  const baseClasses = 'relative p-2 border-2 rounded-lg transition-all duration-200';
  const stateClasses = isRunning 
    ? 'animate-pulse scale-105' 
    : '';
  const backgroundClass = isRunning ? 'bg-green-50' : 'bg-white';
  
  const finalClassName = `${baseClasses} ${stateClasses} ${backgroundClass} ${effectiveClassName}`;
  

  return (
    <div
      {...divProps}
      data-node-color={effectiveBorderColor}
      data-node-selected={selected}
      data-node-running={isRunning}
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
      {showFlipButton && selected && (onFlip || autoHandles) && !isRunning && (
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
        <FlowHandle
          key={handle.id || index}
          nodeId={id}
          type={handle.type}
          name={'name' in handle ? handle.name : `${handle.type}-${index}`}
          position={handle.position}
          offset={'offset' in handle ? handle.offset : 50}
          color={handle.className}  // Extract color from className
          style={handle.style}
          className={`${isRunning ? 'animate-pulse' : ''}`}
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
    (prevProps.data && typeof prevProps.data === 'object' && 'flipped' in prevProps.data ? prevProps.data.flipped : false) === 
    (nextProps.data && typeof nextProps.data === 'object' && 'flipped' in nextProps.data ? nextProps.data.flipped : false) &&
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