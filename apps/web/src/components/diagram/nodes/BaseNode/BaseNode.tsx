import React, { useMemo, useCallback, useEffect, useRef } from 'react';
import { Position, useUpdateNodeInternals } from '@xyflow/react';
import { RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/buttons';
import { getNodeConfig } from '@/config/helpers';
import { FlowHandle } from '@/components/diagram/controls';
import { useCanvasOperations, useExecution } from '@/hooks';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import {NodeKind, nodeId} from '@/types';
import './BaseNode.css';

// Unified props for the single node renderer
interface BaseNodeProps {
  id: string;
  type: string;
  selected?: boolean;
  data: Record<string, unknown>;
  showFlipButton?: boolean;
  className?: string;
}

// Custom hook for node execution status
function useNodeStatus(nodeId: string) {
  const { getNodeExecutionState } = useExecution();
  const nodeState = getNodeExecutionState(nodeId);
  
  return useMemo(() => ({
    isRunning: nodeState?.status === 'running',
    isSkipped: nodeState?.status === 'skipped',
    isCompleted: nodeState?.status === 'completed',
    hasError: nodeState?.status === 'error',
    progress: nodeState?.progress,
    error: nodeState?.error,
  }), [nodeState]);
}

// Custom hook for handles generation
function useHandles(nodeId: string, nodeType: string, isFlipped: boolean) {
  const config = getNodeConfig(nodeType as NodeKind);
  
  return useMemo(() => {
    const allHandles = [
      ...(config.handles.output || []).map(handle => ({ ...handle, type: 'output' as const })),
      ...(config.handles.input || []).map(handle => ({ ...handle, type: 'input' as const }))
    ];
    
    return allHandles.map((handle) => {
      const isVertical = handle.position === 'top' || handle.position === 'bottom';
      const position = isFlipped && !isVertical
        ? (handle.position === 'left' ? Position.Right : Position.Left)
        : (handle.position === 'left' ? Position.Left : 
           handle.position === 'right' ? Position.Right :
           handle.position === 'top' ? Position.Top : Position.Bottom);
      
      const offset = handle.offset || { x: 0, y: 0 };
      const offsetPercentage = isVertical 
        ? 50 + (offset.x / 2)
        : 50 + (offset.y / 2);
      
      const handleName = handle.id || 'default';
      // Generate unique ID by combining nodeId, handle type, and handleName
      const uniqueId = `${nodeId}:${handle.type}:${handleName}`;
      
      return {
        type: handle.type,
        position,
        id: uniqueId,
        name: handleName,
        style: {},
        offset: offsetPercentage,
        color: handle.color
      };
    });
  }, [nodeId, config, isFlipped]);
}

// Memoized status indicator component
const StatusIndicator = React.memo(({ status }: { status: ReturnType<typeof useNodeStatus> }) => {
  if (status.isRunning) {
    return (
      <>
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-ping" />
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full" />
      </>
    );
  }
  
  if (status.hasError) {
    return (
      <div className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 rounded-full">
        <span className="absolute inset-0 text-white text-xs flex items-center justify-center">!</span>
      </div>
    );
  }
  
  if (status.isCompleted) {
    return (
      <div className="absolute -top-2 -right-2 w-4 h-4 bg-blue-500 rounded-full">
        <span className="absolute inset-0 text-white text-xs flex items-center justify-center">✓</span>
      </div>
    );
  }
  
  if (status.isSkipped) {
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
});
StatusIndicator.displayName = 'StatusIndicator';

// Memoized node header component
const NodeHeader = React.memo(({ 
  icon, 
  label, 
  id, 
  configLabel,
  isExecutionMode 
}: { 
  icon: string;
  label?: string;
  id: string;
  configLabel: string;
  isExecutionMode: boolean;
}) => (
  <div className="flex items-center gap-2 mb-2">
    <span className="text-lg">{icon}</span>
    <span className={`font-medium text-sm ${isExecutionMode ? 'text-gray-900' : ''}`}>
      {label || `${configLabel} ${id}`}
    </span>
  </div>
));
NodeHeader.displayName = 'NodeHeader';

// Memoized node body component
const NodeBody = React.memo(({ 
  data, 
  isExecutionMode 
}: { 
  data: Array<[string, unknown]>;
  isExecutionMode: boolean;
}) => (
  <div className="space-y-1">
    {data.map(([key, value]) => {
      // Skip rendering objects
      if (typeof value === 'object' && value !== null) {
        return null;
      }
      
      const displayValue = typeof value === 'string' && value.length > 20 
        ? `${value.substring(0, 20)}...` 
        : String(value);
      
      return (
        <div key={key} className={`text-xs ${isExecutionMode ? 'text-gray-700 font-medium' : 'text-gray-600'}`}>
          {displayValue}
        </div>
      );
    })}
  </div>
));
NodeBody.displayName = 'NodeBody';

export function BaseNode({ 
  id,
  type, 
  selected, 
  data, 
  showFlipButton = true,
  className 
}: BaseNodeProps) {
  // Store selectors
  const canvas = useCanvasOperations();
  const updateNodeInternals = useUpdateNodeInternals();
  const { activeCanvas } = useUnifiedStore();
  const isExecutionMode = activeCanvas === 'execution';
  
  // Use custom hooks
  const nId = nodeId(id);
  const status = useNodeStatus(id);
  const config = getNodeConfig(type as NodeKind);
  const isFlipped = data?.flipped === true;
  const handles = useHandles(id, type, isFlipped);
  
  // Handle flip
  const handleFlip = useCallback(() => {
    canvas.updateNode(nId, { data: { ...data, flipped: !isFlipped } });
    updateNodeInternals(id);
  }, [nId, id, data, isFlipped, canvas, updateNodeInternals]);

  // Track previous data to detect changes
  const prevDataRef = useRef(data);
  
  // Update node internals when data changes (except on first render)
  useEffect(() => {
    // Skip the first render
    if (prevDataRef.current !== data) {
      // Update node internals to recalculate handle positions and connections
      updateNodeInternals(id);
      prevDataRef.current = data;
    }
  }, [data, id, updateNodeInternals]);
  
  // Determine node appearance based on state using data attributes
  const nodeClassNames = useMemo(() => {
    const baseClasses = 'relative p-3 border-2 rounded-lg transition-all duration-200 min-w-32';
    const executionClasses = isExecutionMode ? 'shadow-lg' : 'shadow-sm';
    return `${baseClasses} ${executionClasses} ${className || ''}`;
  }, [isExecutionMode, className]);
  
  // Memoize data attributes for dynamic styling
  const dataAttributes = useMemo(() => ({
    'data-running': status.isRunning,
    'data-error': status.hasError,
    'data-completed': status.isCompleted,
    'data-skipped': status.isSkipped,
    'data-selected': selected,
    'data-color': config.color,
    'data-execution': isExecutionMode,
  }), [status, selected, config.color, isExecutionMode]);
  
  // Get node display data
  const displayData = useMemo(() => {
    const entries = Object.entries(data).filter(([key]) => 
      !['id', 'type', 'flipped', 'x', 'y', 'width', 'height', 'prompt', 'defaultPrompt', 'firstOnlyPrompt', 'promptMessage', 'label', 'name'].includes(key)
    );
    
    return entries.slice(0, 3); // Limit to 3 fields for cleaner display
  }, [data]);

  return (
    <div
      className={nodeClassNames}
      title={status.progress || `${config.label} Node`}
      {...dataAttributes}
    >
      {/* Status indicators */}
      <StatusIndicator status={status} />
      
      {/* Flip button */}
      {selected && showFlipButton && !status.isRunning && (
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
      <div className={status.isRunning ? 'relative z-10' : ''}>
        {/* Header */}
        <NodeHeader 
          icon={config.icon}
          label={String(data.label || data.name || '')}
          id={id}
          configLabel={config.label}
          isExecutionMode={isExecutionMode}
        />
        
        {/* Node data display */}
        <NodeBody data={displayData} isExecutionMode={isExecutionMode} />
        
        {/* Progress or error message */}
        {(status.progress || status.error) && (
          <div className="mt-2 text-xs text-gray-500 italic">
            {status.progress || status.error}
          </div>
        )}
        
        {/* Progress bar for running state */}
        {status.isRunning && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-green-500 animate-pulse rounded-b" />
        )}
      </div>

      {/* Handles */}
      {handles.map((handle) => (
        <FlowHandle
          key={handle.id}
          nodeId={nId}
          type={handle.type}
          label={handle.name}
          position={handle.position}
          offset={handle.offset}
          color={handle.color}
          className={status.isRunning ? 'animate-pulse' : ''}
        />
      ))}
    </div>
  );
}