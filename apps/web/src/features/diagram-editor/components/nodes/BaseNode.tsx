import React, { useMemo, useCallback } from 'react';
import { Position, useUpdateNodeInternals } from '@xyflow/react';
import { RotateCcw } from 'lucide-react';
import { Button } from '@/shared/components/ui/buttons';
import { getNodeConfig } from '@/core/config/helpers';
import { FlowHandle } from '@/features/diagram-editor/components/controls';
import { useNodeOperations } from '../../hooks';
import { useCanvasOperationsContext } from '../../contexts/CanvasContext';
import { useUIState } from '@/shared/hooks/selectors';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { NodeType, NodeExecutionStatus } from '@dipeo/domain-models';
import { nodeId } from '@/core/types';
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
function useNodeStatus(nodeIdStr: string) {
  // Get execution state directly from the store for real-time updates
  const nodeExecutionState = useUnifiedStore(state => {
    const nId = nodeId(nodeIdStr);
    return state.execution.nodeStates.get(nId);
  });
  
  // Also get from executionOps for hook state (progress, etc)
  const { executionOps } = useCanvasOperationsContext();
  const hookNodeState = executionOps.getNodeExecutionState(nodeId(nodeIdStr));
  
  return useMemo(() => ({
    isRunning: nodeExecutionState?.status === NodeExecutionStatus.RUNNING || hookNodeState?.status === 'running',
    isSkipped: nodeExecutionState?.status === NodeExecutionStatus.SKIPPED || hookNodeState?.status === 'skipped',
    isCompleted: nodeExecutionState?.status === NodeExecutionStatus.COMPLETED || hookNodeState?.status === 'completed',
    hasError: nodeExecutionState?.status === NodeExecutionStatus.FAILED || hookNodeState?.status === 'error',
    progress: hookNodeState?.progress,
    error: nodeExecutionState?.error || hookNodeState?.error,
  }), [nodeExecutionState, hookNodeState]);
}

// Custom hook for handles generation with auto-spacing
function useHandles(nodeId: string, nodeType: string, isFlipped: boolean) {
  const config = getNodeConfig(nodeType as NodeType);
  
  return useMemo(() => {
    const allHandles = [
      ...(config.handles.output || []).map(handle => ({ ...handle, type: 'output' as const })),
      ...(config.handles.input || []).map(handle => ({ ...handle, type: 'input' as const }))
    ];
    
    // Group handles by position to calculate auto-spacing
    const handlesByPosition = allHandles.reduce((acc, handle) => {
      const pos = handle.position || 'right';
      if (!acc[pos]) acc[pos] = [];
      acc[pos].push(handle);
      return acc;
    }, {} as Record<string, typeof allHandles>);
    
    // Process each handle with proper spacing
    const processedHandles: Array<{
      type: 'input' | 'output';
      position: Position;
      id: string;
      name: string;
      style: Record<string, unknown>;
      offset: number;
      color?: string;
    }> = [];
    
    Object.entries(handlesByPosition).forEach(([pos, handles]) => {
      const count = handles.length;
      
      handles.forEach((handle, index) => {
        const isVertical = pos === 'top' || pos === 'bottom';
        const position = isFlipped && !isVertical
          ? (handle.position === 'left' ? Position.Right : Position.Left)
          : (handle.position === 'left' ? Position.Left : 
             handle.position === 'right' ? Position.Right :
             handle.position === 'top' ? Position.Top : Position.Bottom);
        
        let offsetPercentage: number;
        
        if (handle.offset) {
          // Use explicit offset with better scaling for pill-shaped handles
          const offset = handle.offset;
          const scaleFactor = 0.8; // Increased from 0.5 to give more spacing
          offsetPercentage = isVertical 
            ? 50 + (offset.x * scaleFactor)
            : 50 + (offset.y * scaleFactor);
        } else {
          // Auto-space handles when no offset is defined
          if (count === 1) {
            offsetPercentage = 50;
          } else {
            // Distribute evenly with padding from edges
            const padding = 35; // significantly increased percentage from edge for better spacing
            const availableSpace = 100 - (2 * padding);
            const spacing = availableSpace / (count - 1);
            offsetPercentage = padding + (index * spacing);
          }
        }
        
        const handleName = handle.id || 'default';
        // Generate unique ID by combining nodeId, handle type, and handleName
        const uniqueId = `${nodeId}:${handle.type}:${handleName}`;
        
        processedHandles.push({
          type: handle.type,
          position,
          id: uniqueId,
          name: handle.label || handleName,
          style: {},
          offset: offsetPercentage,
          color: handle.color
        });
      });
    });
    
    return processedHandles;
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
      <div className="absolute -top-2 -right-2 w-4 h-4 bg-purple-600 rounded-full">
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
  configLabel,
  _isExecutionMode 
}: { 
  icon: string;
  label?: string;
  configLabel: string;
  _isExecutionMode: boolean;
}) => (
  <div className="flex items-center justify-center gap-2 mb-2">
    <span className="text-xl">{icon}</span>
    <span className="font-medium text-base text-black">
      {label || configLabel}
    </span>
  </div>
));
NodeHeader.displayName = 'NodeHeader';

// Memoized node body component
const NodeBody = React.memo(({ 
  data, 
  _isExecutionMode 
}: { 
  data: Array<[string, unknown]>;
  _isExecutionMode: boolean;
}) => (
  <div className="space-y-1">
    {data.map(([key, value]) => {
      // Skip rendering objects
      if (typeof value === 'object' && value !== null) {
        return null;
      }
      
      // Special handling for conditionType - use emojis
      if (key === 'conditionType') {
        const emoji = value === 'expression' ? '📝' : 
                     value === 'detect_max_iterations' ? '🔄' : 
                     value === 'simple' ? '✓' : 
                     value === 'complex' ? '⚙️' : '🔀';
        const displayText = value === 'detect_max_iterations' ? 'Max Iter' : String(value);
        return (
          <div key={key} className="text-sm text-black font-medium text-center">
            <span className="text-xs text-gray-500">type:</span> {emoji} {displayText}
          </div>
        );
      }
      
      // Special handling for forgettingMode - use emojis
      if (key === 'forgettingMode') {
        const emoji = value === 'keep_first' ? '📌' : 
                     value === 'keep_last' ? '📍' : 
                     value === 'summarize' ? '📄' : '❓';
        return (
          <div key={key} className="text-sm text-black font-medium text-center">
            <span className="text-xs text-gray-500">mode:</span> {emoji} {String(value)}
          </div>
        );
      }
      
      const displayValue = typeof value === 'string' && value.length > 20 
        ? `${value.substring(0, 20)}...` 
        : String(value);
      
      return (
        <div key={key} className="text-sm text-black font-medium text-center">
          <span className="text-xs text-gray-500">{key}:</span> {displayValue}
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
  const { updateNode } = useNodeOperations();
  const updateNodeInternals = useUpdateNodeInternals();
  const { activeCanvas } = useUIState();
  const isExecutionMode = activeCanvas === 'execution';
  
  // Get selected person from store to highlight person_job nodes
  const selectedPersonId = useUnifiedStore(state => 
    state.selectedType === 'person' ? state.selectedId : null
  );
  
  // Use custom hooks
  const nId = nodeId(id);
  const status = useNodeStatus(id);
  const config = getNodeConfig(type as NodeType);
  const isFlipped = data?.flipped === true;
  const handles = useHandles(id, type, isFlipped);
  
  // Handle flip
  const handleFlip = useCallback(() => {
    updateNode(nId, { data: { ...data, flipped: !isFlipped } });
    updateNodeInternals(id);
  }, [nId, id, data, isFlipped, updateNode, updateNodeInternals]);
  
  // Check if this person_job node is assigned to the selected person
  const isAssignedToSelectedPerson = useMemo(() => {
    return type === 'person_job' && 
           selectedPersonId && 
           data?.person === selectedPersonId;
  }, [type, selectedPersonId, data?.person]);

  
  // Determine node appearance based on state using data attributes
  const nodeClassNames = useMemo(() => {
    // Smaller sizing for start and endpoint nodes
    const isSmallNode = type === 'start' || type === 'endpoint';
    const padding = isSmallNode ? 'p-4' : 'p-5';
    const minWidth = isSmallNode ? 'min-w-40' : 'min-w-48';
    
    const baseClasses = `relative ${padding} border-2 rounded-lg transition-all duration-200 ${minWidth}`;
    const executionClasses = isExecutionMode ? 'shadow-lg' : 'shadow-sm';
    return `${baseClasses} ${executionClasses} ${className || ''}`;
  }, [type, isExecutionMode, className]);
  
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
    const entries = Object.entries(data).filter(([key, value]) => 
      // Filter out system keys and personId
      !['id', 'type', 'flipped', 'x', 'y', 'width', 'height', 'prompt', 'defaultPrompt', 'firstOnlyPrompt', 'promptMessage', 'label', 'name', 'personId'].includes(key) &&
      // Filter out blank values (null, undefined, empty string)
      value !== null && value !== undefined && value !== ''
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
      
      {/* Person assignment indicator */}
      {isAssignedToSelectedPerson && (
        <div className="absolute -top-3 -left-3 w-8 h-8 bg-purple-500 rounded-full animate-pulse flex items-center justify-center">
          <span className="text-white text-lg">👤</span>
        </div>
      )}
      
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
          configLabel={config.label}
          _isExecutionMode={isExecutionMode}
        />
        
        {/* Node data display - only show if there's data to display */}
        {displayData.length > 0 && (
          <NodeBody data={displayData} _isExecutionMode={isExecutionMode} />
        )}
        
        {/* Progress or error message */}
        {(status.progress || status.error) && (
          <div className="mt-2 text-sm text-black italic text-center">
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
          nodeType={type}
          className={status.isRunning ? 'animate-pulse' : ''}
        />
      ))}
    </div>
  );
}