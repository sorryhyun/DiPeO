import React, { useMemo, useCallback, useState } from 'react';
import { Position, useUpdateNodeInternals } from '@xyflow/react';
import { ArrowUp, ArrowRight } from 'lucide-react';
import { Button } from '@/shared/components/forms/buttons';
import { getNodeConfig } from '@/features/diagram-editor/config/nodes';
import { FlowHandle } from '@/features/diagram-editor/components/controls';
import { useCanvasOperations } from '@/shared/contexts/CanvasContext';
import { useUIState } from '@/core/store/hooks/state';
import { useNodeExecutionData, useSelectionData, usePersonData, useNodeOperations } from '@/core/store/hooks';
import { NodeType, NodeExecutionStatus, nodeId, personId } from '@/core/types';
import './BaseNode.css';

// Unified props for the single node renderer
interface BaseNodeProps {
  id: string;
  type: string;
  selected?: boolean;
  data: Record<string, unknown>;
  showFlipButton?: boolean;
  className?: string;
  dragging?: boolean;
}

// Custom hook for node execution status
function useNodeStatus(nodeIdStr: string) {
  // Get execution state directly from the store for real-time updates
  const nId = nodeId(nodeIdStr);
  const nodeExecutionState = useNodeExecutionData(nId);
  
  // Also get from executionOps for hook state (progress, etc)
  const operations = useCanvasOperations();
  const hookNodeState = operations.executionOps.getNodeExecutionState(nodeId(nodeIdStr));
  
  return useMemo(() => ({
    isRunning: nodeExecutionState?.status === NodeExecutionStatus.RUNNING || hookNodeState?.status === 'running',
    isSkipped: nodeExecutionState?.status === NodeExecutionStatus.SKIPPED || hookNodeState?.status === 'skipped',
    isCompleted: nodeExecutionState?.status === NodeExecutionStatus.COMPLETED || nodeExecutionState?.status === NodeExecutionStatus.MAXITER_REACHED || hookNodeState?.status === 'completed',
    hasError: nodeExecutionState?.status === NodeExecutionStatus.FAILED || hookNodeState?.status === 'error',
    isMaxIterReached: nodeExecutionState?.status === NodeExecutionStatus.MAXITER_REACHED,
    progress: hookNodeState?.progress,
    error: nodeExecutionState?.error || hookNodeState?.error,
  }), [nodeExecutionState, hookNodeState]);
}

// Custom hook for handles generation with auto-spacing
function useHandles(nodeId: string, nodeType: string, flippedState: { horizontal: boolean; vertical: boolean }) {
  const config = getNodeConfig(nodeType as NodeType);
  
  return useMemo(() => {
    if (!config) return [];
    
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
      handleId: string;
      name: string;
      style: Record<string, unknown>;
      offset: number;
      color?: string;
    }> = [];
    
    Object.entries(handlesByPosition).forEach(([pos, handles]) => {
      const count = handles.length;
      
      handles.forEach((handle, index) => {
        const isVertical = pos === 'top' || pos === 'bottom';
        const isHorizontal = pos === 'left' || pos === 'right';
        
        // Apply flips to positions
        let position = handle.position === 'left' ? Position.Left : 
                      handle.position === 'right' ? Position.Right :
                      handle.position === 'top' ? Position.Top : Position.Bottom;
        
        // Apply horizontal flip (swap left/right)
        if (flippedState.horizontal && isHorizontal) {
          position = position === Position.Left ? Position.Right : Position.Left;
        }
        
        // Apply vertical flip (swap top/bottom)
        if (flippedState.vertical && isVertical) {
          position = position === Position.Top ? Position.Bottom : Position.Top;
        }
        
        // When vertical flip is active, reverse the order of handles on horizontal sides
        let effectiveIndex = index;
        if (flippedState.vertical && isHorizontal) {
          effectiveIndex = count - 1 - index;
        }
        
        let offsetPercentage: number;
        
        if (handle.offset) {
          // Use explicit offset with better scaling for pill-shaped handles
          const offset = handle.offset;
          const scaleFactor = 0.8; // Increased from 0.5 to give more spacing
          
          // When vertical flip is active, also invert the offset on horizontal sides
          if (flippedState.vertical && isHorizontal) {
            offsetPercentage = 50 - (offset.y * scaleFactor);
          } else {
            offsetPercentage = isVertical 
              ? 50 + (offset.x * scaleFactor)
              : 50 + (offset.y * scaleFactor);
          }
        } else {
          // Auto-space handles when no offset is defined
          if (count === 1) {
            offsetPercentage = 50;
          } else {
            // Distribute evenly with padding from edges
            const padding = 35; // significantly increased percentage from edge for better spacing
            const availableSpace = 100 - (2 * padding);
            const spacing = availableSpace / (count - 1);
            offsetPercentage = padding + (effectiveIndex * spacing);
          }
        }
        
        const handleName = handle.label || 'default';
        const uniqueId = `${nodeId}_${handle.type}_${handleName}`;
        
        processedHandles.push({
          type: handle.type,
          position,
          id: uniqueId,
          handleId: handleName, // The actual handle ID (e.g., 'condtrue', 'condfalse')
          name: handle.label || handleName, // The display label (e.g., 'true', 'false')
          style: {},
          offset: offsetPercentage,
          color: handle.color
        });
      });
    });
    
    return processedHandles;
  }, [nodeId, config, flippedState]);
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
  
  // MAXITER_REACHED is now treated as completed, so no special indicator needed
  
  return null;
});
StatusIndicator.displayName = 'StatusIndicator';

// Memoized node header component
const NodeHeader = React.memo(({ 
  icon, 
  label, 
  configLabel,
  _isExecutionMode,
  memoryEmoji 
}: { 
  icon: string;
  label?: string;
  configLabel: string;
  _isExecutionMode: boolean;
  memoryEmoji?: string;
}) => (
  <div className="flex items-center justify-center gap-2 mb-2">
    <span className="text-xl">{icon}</span>
    <span className="font-medium text-base text-black">
      {label || configLabel}
    </span>
    {memoryEmoji && (
      <span className="text-lg" title="Memory Profile">{memoryEmoji}</span>
    )}
  </div>
));
NodeHeader.displayName = 'NodeHeader';

// Memoized node body component
const NodeBody = React.memo(({ 
  data, 
  _isExecutionMode,
  isExpanded 
}: { 
  data: Array<[string, unknown]>;
  _isExecutionMode: boolean;
  isExpanded: boolean;
}) => {
  // Special formatting for known value types
  const formatValue = (key: string, value: unknown): React.ReactNode => {
    // Special handling for conditionType - use only emojis
    if (key === 'condition_type') {
      const emoji = value === 'expression' ? '📝' : 
                   value === 'detect_max_iterations' ? '🔄' : 
                   value === 'simple' ? '✓' : 
                   value === 'complex' ? '⚙️' : '🔀';
      return <span className="text-lg">{emoji}</span>;
    }
    
    // Special handling for memory_settings.view - use emojis
    if (key === 'memory_settings.view' || (key === 'memory_settings' && typeof value === 'object' && value && 'view' in value)) {
      const viewValue = key === 'memory_settings.view' ? value : (value as any).view;
      const emoji = viewValue === 'all_involved' ? '🧠' :
                   viewValue === 'sent_by_me' ? '📤' :
                   viewValue === 'sent_to_me' ? '📥' :
                   viewValue === 'system_and_me' ? '💭' :
                   viewValue === 'conversation_pairs' ? '🎯' : '❓';
      return <span className="text-lg" title={`Memory View: ${viewValue}`}>{emoji}</span>;
    }
    
    // Special handling for boolean values
    if (typeof value === 'boolean') {
      return <span className="text-sm">{value ? '✓' : '✗'}</span>;
    }
    
    // Format other values
    const displayValue = typeof value === 'string' && value.length > 20 
      ? `${value.substring(0, 20)}...` 
      : String(value);
    
    return <span className="text-sm font-medium">{displayValue}</span>;
  };
  
  // Format key names for better display
  const formatKey = (key: string): string => {
    return key.replace(/_/g, ' ').replace(/\./g, ' ').split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  return (
    <div className="space-y-1 transition-all duration-200">
      {data.map(([key, value], index) => {
        // Skip rendering objects
        if (typeof value === 'object' && value !== null && key !== 'memory_settings') {
          return null;
        }
        
        // Skip memory_profile as it's now shown in the header
        if (key === 'memory_profile') {
          return null;
        }
        
        // For single prop display (not expanded), center it
        if (!isExpanded && data.length === 1) {
          return (
            <div key={key} className="text-center">
              {formatValue(key, value)}
            </div>
          );
        }
        
        // For expanded view, show key-value pairs
        return (
          <div 
            key={key} 
            className={`text-sm text-black flex items-center justify-center gap-1 ${
              index > 0 ? 'node-body-content' : ''
            }`}
          >
            <span className="text-xs text-gray-500">{formatKey(key)}:</span>
            {formatValue(key, value)}
          </div>
        );
      })}
    </div>
  );
});
NodeBody.displayName = 'NodeBody';

export function BaseNode({ 
  id,
  type, 
  selected, 
  data, 
  showFlipButton = true,
  className,
  dragging = false
}: BaseNodeProps) {
  // Local state
  const [isHovered, setIsHovered] = useState(false);
  
  // Use dragging state to override hover
  const effectiveHover = dragging || isHovered;
  
  // Store selectors
  const nodeOps = useNodeOperations();
  const updateNodeInternals = useUpdateNodeInternals();
  const { activeCanvas } = useUIState();
  const isExecutionMode = activeCanvas === 'execution';
  
  // Get selected person from store to highlight person_job nodes
  const { selectedId, selectedType } = useSelectionData();
  const selectedPersonId = selectedType === 'person' ? selectedId : null;
  
  // Get person label for person_job nodes
  const assignedPersonId = type === 'person_job' && data?.person ? personId(String(data.person)) : null;
  const assignedPerson = usePersonData(assignedPersonId);
  const personLabel = assignedPerson?.label || '';
  
  // Use custom hooks
  const nId = nodeId(id);
  const status = useNodeStatus(id);
  const config = getNodeConfig(type as NodeType);
  
  // Handle flipped state - support both legacy boolean and new array format
  const flippedState = useMemo(() => {
    if (Array.isArray(data?.flipped)) {
      return { horizontal: data.flipped[0] || false, vertical: data.flipped[1] || false };
    } else if (typeof data?.flipped === 'boolean') {
      // Legacy support: old boolean flipped is horizontal flip
      return { horizontal: data.flipped, vertical: false };
    }
    return { horizontal: false, vertical: false };
  }, [data?.flipped]);
  
  const handles = useHandles(id, type, flippedState);
  
  // Handle horizontal flip
  const handleFlipHorizontal = useCallback(() => {
    const newFlipped = [!flippedState.horizontal, flippedState.vertical];
    nodeOps.updateNode(nId, { data: { ...data, flipped: newFlipped } });
    updateNodeInternals(id);
  }, [nId, id, data, flippedState, nodeOps, updateNodeInternals]);
  
  // Handle vertical flip
  const handleFlipVertical = useCallback(() => {
    const newFlipped = [flippedState.horizontal, !flippedState.vertical];
    nodeOps.updateNode(nId, { data: { ...data, flipped: newFlipped } });
    updateNodeInternals(id);
  }, [nId, id, data, flippedState, nodeOps, updateNodeInternals]);
  
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
    
    const baseClasses = `relative ${padding} border-2 rounded-lg ${minWidth}`;
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
    'data-color': config?.color,
    'data-execution': isExecutionMode,
  }), [status, selected, config?.color, isExecutionMode]);
  
  // Get primary display field from node config
  const primaryDisplayField = useMemo(() => {
    return config?.primaryDisplayField || null;
  }, [config]);

  // Get node display data
  const displayData = useMemo(() => {
    // Define fields that contain long text and should be excluded
    const longTextFields = [
      'prompt', 'defaultPrompt', 'firstOnlyPrompt', 'default_prompt', 
      'first_only_prompt', 'promptMessage', 'code', 'template', 
      'expression', 'description', 'content', 'body', 'schema'
    ];
    
    const entries = Object.entries(data).filter(([key, value]) => {
      // Filter out system keys and long text fields
      return !['id', 'type', 'flipped', 'x', 'y', 'width', 'height', 
              'label', 'name', 'personId', 'person', 'memory_config', 
              'memory_config.forget_mode', ...longTextFields].includes(key) &&
        // Filter out blank values (null, undefined, empty string)
        value !== null && value !== undefined && value !== '';
    });
    
    // Add person label display for person_job nodes
    if (type === 'person_job' && personLabel) {
      entries.unshift(['person', personLabel]);
    }
    
    // Add memory_config.forget_mode for person_job nodes
    if (type === 'person_job' && data['memory_config.forget_mode']) {
      entries.push(['memory_config.forget_mode', data['memory_config.forget_mode']]);
    }
    
    // When not hovered, show only the primary display field
    if (!effectiveHover && primaryDisplayField) {
      const importantEntry = entries.find(([key]) => key === primaryDisplayField);
      if (importantEntry) {
        return [importantEntry];
      }
      // If primary display field not found, show first entry
      return entries.slice(0, 1);
    }
    
    // When hovered, show up to 3 fields
    return entries.slice(0, 3);
  }, [data, type, personLabel, effectiveHover, primaryDisplayField]);

  return (
    <div
      className={nodeClassNames}
      title={status.progress || `${config?.label || 'Unknown'} Node`}
      onMouseEnter={() => !dragging && setIsHovered(true)}
      onMouseLeave={() => !dragging && setIsHovered(false)}
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
      
      {/* Flip buttons */}
      {effectiveHover && showFlipButton && !status.isRunning && (
        <>
          {/* Flip horizontal button - swaps left/right handles */}
          <Button
            onClick={handleFlipHorizontal}
            variant="outline"
            size="icon"
            className={`absolute -top-10 left-1/2 transform -translate-x-1/2 w-8 h-8 rounded-full shadow-md ${
              flippedState.horizontal ? 'bg-blue-100 hover:bg-blue-200' : 'bg-white hover:bg-gray-50'
            }`}
            title="Flip handles left/right"
            style={{ marginLeft: '-20px' }}
          >
            <ArrowRight className="w-4 h-4" />
          </Button>
          
          {/* Flip vertical button - swaps top/bottom handles */}
          <Button
            onClick={handleFlipVertical}
            variant="outline"
            size="icon"
            className={`absolute -top-10 left-1/2 transform -translate-x-1/2 w-8 h-8 rounded-full shadow-md ${
              flippedState.vertical ? 'bg-blue-100 hover:bg-blue-200' : 'bg-white hover:bg-gray-50'
            }`}
            title="Flip handles up/down"
            style={{ marginLeft: '20px' }}
          >
            <ArrowUp className="w-4 h-4" />
          </Button>
        </>
      )}

      {/* Node content */}
      <div className={status.isRunning ? 'relative z-10' : ''}>
        {/* Header */}
        <NodeHeader 
          icon={config?.icon || '📦'}
          label={String(data.label || data.name || '')}
          configLabel={config?.label || 'Node'}
          _isExecutionMode={isExecutionMode}
          memoryEmoji={type === 'person_job' && data.memory_profile ? (
            data.memory_profile === 'FULL' ? '🧠' :
            data.memory_profile === 'FOCUSED' ? '🎯' :
            data.memory_profile === 'MINIMAL' ? '💭' :
            data.memory_profile === 'GOLDFISH' ? '🐠' :
            data.memory_profile === 'CUSTOM' ? '⚙️' : undefined
          ) : undefined}
        />
        
        {/* Node data display - only show if there's data to display */}
        {displayData.length > 0 && (
          <NodeBody data={displayData} _isExecutionMode={isExecutionMode} isExpanded={effectiveHover} />
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
          handleId={handle.handleId}
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