import React from 'react';
import { Position, useUpdateNodeInternals } from '@xyflow/react';
import { RotateCcw } from 'lucide-react';
import { Button } from '@/common/components';
import { getNodeConfig } from '@/config/nodes';
import { createHandleId } from '@/features/nodes/utils/nodeHelpers';
import { FlowHandle } from './FlowHandle';
import { useDiagramStore, useAppStore } from '@/state/stores';
import './BaseNode.css';

// Simplified props - no more prop drilling
interface BaseNodeProps {
  id: string;
  type: string;
  selected?: boolean;
  data: Record<string, any>;
}

export function BaseNode({ id, type, selected, data }: BaseNodeProps) {
  // Direct store access
  const updateNode = useDiagramStore(state => state.updateNode);
  const updateNodeInternals = useUpdateNodeInternals();
  
  // Execution state
  const isNodeRunning = useAppStore(state => state.isNodeRunning);
  const isRunning = isNodeRunning(id);
  
  // For now, we'll handle skipped state later when we refactor execution
  const isSkipped = false;
  const skippedInfo = null;
  
  // Node configuration
  const config = getNodeConfig(type);
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
        offset: 50, // Default offset for compatibility
        className: handle.color || ''
      };
    });
  }, [config, id, isFlipped]);
  
  // Handle flip
  const handleFlip = React.useCallback(() => {
    updateNode(id, { ...data, flipped: !isFlipped });
    updateNodeInternals(id);
  }, [id, data, isFlipped, updateNode, updateNodeInternals]);
  

  // Apply base classes with data attributes for dynamic styling
  const baseClasses = 'relative p-2 border-2 rounded-lg transition-all duration-200';
  const stateClasses = isRunning 
    ? 'animate-pulse scale-105' 
    : isSkipped 
    ? 'opacity-75'
    : '';
  const backgroundClass = isRunning 
    ? 'bg-green-50' 
    : isSkipped 
    ? 'bg-yellow-50' 
    : 'bg-white';
  
  const borderColorClass = `border-${config.color}-500`;
  const className = `${baseClasses} ${stateClasses} ${backgroundClass} ${borderColorClass}`;

  return (
    <div
      data-node-color={borderColorClass}
      data-node-selected={selected}
      data-node-running={isRunning}
      data-node-skipped={isSkipped}
      className={className}
      title={isSkipped ? `Skipped: ${skippedInfo?.reason}` : undefined}
    >
      {/* Add multiple visual indicators for running state */}
      {isRunning && (
        <>
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-ping" />
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full" />
          <div className="absolute inset-0 bg-green-100 opacity-20 rounded-lg animate-pulse" />
        </>
      )}
      
      {/* Visual indicators for skipped state */}
      {isSkipped && (
        <>
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-500 rounded-full" />
          <div className="absolute inset-0 bg-yellow-100 opacity-20 rounded-lg" />
          <div className="absolute top-1 right-1 text-xs text-yellow-700 font-medium">
            SKIPPED
          </div>
        </>
      )}
      
      {/* Flip button */}
      {selected && !isRunning && (
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
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">{config.icon}</span>
          <span className="font-medium">{config.label}</span>
        </div>
        
        {/* Display key node data */}
        {Object.entries(data).map(([key, value]) => {
          if (key === 'id' || key === 'type' || key === 'flipped') return null;
          return (
            <div key={key} className="text-xs text-gray-600 truncate">
              {key}: {String(value)}
            </div>
          );
        })}
        
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
          className={`${isRunning ? 'animate-pulse' : ''}`}
        />
      ))}
    </div>
  );
}