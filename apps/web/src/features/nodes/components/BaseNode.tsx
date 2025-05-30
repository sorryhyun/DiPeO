import React from 'react';
import { BaseNode as BaseNodeComponent, GenericNode as GenericNodeComponent } from '@/features/diagram/wrappers';
import { useNodeExecutionState } from '@/shared/hooks/useStoreSelectors';
import { useDiagramContext } from '@/shared/contexts/DiagramContext';

// Re-export types from local types
export type { BaseNodeProps } from '../../../shared/types';

// Memoized wrapper component that integrates with app stores
export const BaseNode = React.memo((props: Parameters<typeof BaseNodeComponent>[0]) => {
  const { id } = props;
  
  // Use optimized selectors to prevent unnecessary re-renders
  const { isRunning } = useNodeExecutionState(id);
  const { updateNodeData, updateNodeInternals, nodeConfigs } = useDiagramContext();
  
  return (
    <BaseNodeComponent
      {...props}
      isRunning={isRunning}
      onUpdateData={updateNodeData}
      onUpdateNodeInternals={updateNodeInternals}
      nodeConfigs={nodeConfigs}
    />
  );
}, (prevProps, nextProps) => {
  // Only re-render if id or other critical props change
  return (
    prevProps.id === nextProps.id &&
    prevProps.selected === nextProps.selected &&
    JSON.stringify(prevProps.data) === JSON.stringify(nextProps.data)
  );
});

BaseNode.displayName = 'BaseNodeWrapper';

// Re-export GenericNodeProps type
export type { GenericNodeProps } from '../../../shared/types';

// Memoized wrapper for GenericNode that integrates with app stores
export const GenericNode = React.memo((props: Parameters<typeof GenericNodeComponent>[0]) => {
  const { id } = props;
  
  // Use optimized selectors to prevent unnecessary re-renders
  const { isRunning } = useNodeExecutionState(id);
  const { updateNodeData, updateNodeInternals, nodeConfigs } = useDiagramContext();
  
  return (
    <GenericNodeComponent
      {...props}
      isRunning={isRunning}
      onUpdateData={updateNodeData}
      onUpdateNodeInternals={updateNodeInternals}
      nodeConfigs={nodeConfigs}
    />
  );
}, (prevProps, nextProps) => {
  // Only re-render if id or other critical props change
  return (
    prevProps.id === nextProps.id &&
    prevProps.selected === nextProps.selected &&
    JSON.stringify(prevProps.data) === JSON.stringify(nextProps.data)
  );
});

GenericNode.displayName = 'GenericNodeWrapper';