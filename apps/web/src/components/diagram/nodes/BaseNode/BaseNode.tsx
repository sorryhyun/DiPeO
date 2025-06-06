import React from 'react';
import { Position, useUpdateNodeInternals } from '@xyflow/react';
import { RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/buttons';
import { getNodeConfig } from '@/config/helpers';
import { createHandleId } from '@/utils/node';
import { FlowHandle } from '@/components/diagram/controls';
import { useNodeDataUpdater } from '@/hooks/useStoreSelectors';
import { useRealtimeExecution } from '@/hooks/useRealtimeExecution';
import './BaseNode.css';

// Unified props for the single node renderer
interface BaseNodeProps {
  id: string;
  type: string;
  selected?: boolean;
  data: Record<string, any>;
  showFlipButton?: boolean;
  className?: string;
}

export function BaseNode({ 
  id, 
  type, 
  selected, 
  data, 
  showFlipButton = true,
  className 
}: BaseNodeProps) {
  // Store selectors
  const updateNode = useNodeDataUpdater();
  const updateNodeInternals = useUpdateNodeInternals();
  
  // Get execution state
  const { nodeStates } = useRealtimeExecution();
  const nodeState = nodeStates?.[id];
  const isRunning = nodeState?.status === 'running';
  const isSkipped = nodeState?.status === 'skipped';
  const isCompleted = nodeState?.status === 'completed';
  const hasError = nodeState?.status === 'error';
  
  // Node configuration
  const config = getNodeConfig(type as any);
  const isFlipped = data?.flipped === true;
  
  // Generate handles from config
  const handles = React.useMemo(() => {
    const allHandles = [
      ...(config.handles.output || []).map(handle => ({ ...handle, type: 'output' as const })),
      ...(config.handles.input || []).map(handle => ({ ...handle, type: 'input' as const }))
    ];
    
    return allHandles.map(handle => {
      const isVertical = handle.position === 'top' || handle.position === 'bottom';
      const position = isFlipped && !isVertical
        ? (handle.position === 'left' ? Position.Right : Position.Left)
        : (handle.position === 'left' ? Position.Left : 
           handle.position === 'right' ? Position.Right :
           handle.position === 'top' ? Position.Top : Position.Bottom);
      
      const offset = handle.offset || { x: 0, y: 0 };
      const style = isVertical 
        ? { left: '50%', transform: `translateX(-50%) translateX(${offset.x}px)` }
        : { top: '50%', transform: `translateY(-50%) translateY(${offset.y}px)` };
      
      return {
        type: handle.type,
        position,
        id: createHandleId(id, handle.type, handle.id),
        name: handle.id,
        style,
        offset: 50,
        className: (handle as any).color || ''
      };
    });
  }, [config, id, isFlipped]);
  
  // Handle flip
  const handleFlip = React.useCallback(() => {
    updateNode(id, { ...data, flipped: !isFlipped });
    updateNodeInternals(id);
  }, [id, data, isFlipped, updateNode, updateNodeInternals]);
  
  // Determine node appearance based on state
  const getNodeClasses = () => {
    const baseClasses = 'relative p-3 border-2 rounded-lg transition-all duration-200 min-w-32 shadow-sm';
    let stateClasses = '';
    let backgroundClass = 'bg-white';
    let borderClass = `border-${config.color}-500`;
    
    if (isRunning) {
      stateClasses = 'animate-pulse scale-105';
      backgroundClass = 'bg-green-50';
      borderClass = 'border-green-500';
    } else if (hasError) {
      backgroundClass = 'bg-red-50';
      borderClass = 'border-red-500';
    } else if (isCompleted) {
      backgroundClass = 'bg-blue-50';
      borderClass = 'border-blue-500';
    } else if (isSkipped) {
      stateClasses = 'opacity-75';
      backgroundClass = 'bg-yellow-50';
      borderClass = 'border-yellow-500';
    } else if (selected) {
      borderClass = `border-${config.color}-600`;
      stateClasses = 'ring-2 ring-blue-200';
    }
    
    return `${baseClasses} ${stateClasses} ${backgroundClass} ${borderClass} ${className || ''}`;
  };

  // Get status indicator
  const getStatusIndicator = () => {
    if (isRunning) {
      return (
        <>
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-ping" />
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full" />
        </>
      );
    }
    
    if (hasError) {
      return (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 rounded-full">
          <span className="absolute inset-0 text-white text-xs flex items-center justify-center">!</span>
        </div>
      );
    }
    
    if (isCompleted) {
      return (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-blue-500 rounded-full">
          <span className="absolute inset-0 text-white text-xs flex items-center justify-center">✓</span>
        </div>
      );
    }
    
    if (isSkipped) {
      return (
        <>
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-500 rounded-full" />
          <div className="absolute top-1 right-1 text-xs text-yellow-700 font-medium">
            SKIP
          </div>
        </>
      );
    }
    
    return null;
  };

  // Get node display data
  const getDisplayData = () => {
    const entries = Object.entries(data).filter(([key]) => 
      !['id', 'type', 'flipped', 'x', 'y', 'width', 'height'].includes(key)
    );
    
    // Show most important fields first
    const importantFields = ['label', 'prompt', 'defaultPrompt', 'firstOnlyPrompt'];
    const important = entries.filter(([key]) => importantFields.includes(key));
    const others = entries.filter(([key]) => !importantFields.includes(key));
    
    return [...important, ...others].slice(0, 3); // Limit to 3 fields for cleaner display
  };

  return (
    <div
      className={getNodeClasses()}
      title={nodeState?.progress || `${config.label} Node`}
    >
      {/* Status indicators */}
      {getStatusIndicator()}
      
      {/* Flip button */}
      {selected && showFlipButton && !isRunning && (
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

      {/* Node content */}
      <div className={isRunning ? 'relative z-10' : ''}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">{config.icon}</span>
          <span className="font-medium text-sm">{config.label}</span>
        </div>
        
        {/* Node data display */}
        <div className="space-y-1">
          {getDisplayData().map(([key, value]) => {
            const displayValue = typeof value === 'string' && value.length > 20 
              ? `${value.substring(0, 20)}...` 
              : String(value);
            
            return (
              <div key={key} className="text-xs text-gray-600">
                <span className="font-medium">{key}:</span> {displayValue}
              </div>
            );
          })}
        </div>
        
        {/* Progress or error message */}
        {(nodeState?.progress || nodeState?.error) && (
          <div className="mt-2 text-xs text-gray-500 italic">
            {nodeState.progress || nodeState.error}
          </div>
        )}
        
        {/* Progress bar for running state */}
        {isRunning && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-green-500 animate-pulse rounded-b" />
        )}
      </div>

      {/* Handles */}
      {handles.map((handle: any) => (
        <FlowHandle
          key={handle.id}
          nodeId={id}
          type={handle.type}
          name={handle.name}
          position={handle.position}
          offset={handle.offset}
          color={handle.className}
          style={handle.style}
          className={isRunning ? 'animate-pulse' : ''}
        />
      ))}
    </div>
  );
}