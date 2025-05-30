import React from 'react';
import { useUpdateNodeInternals } from '@xyflow/react';
import { BaseNode as BaseNodeComponent, GenericNode as GenericNodeComponent } from '@repo/diagram-ui';
import { useNodeExecutionState, useNodeDataUpdater } from '@/hooks/useStoreSelectors';
import { getUnifiedNodeConfigsByReactFlowType } from '@repo/core-model';

// Re-export types from diagram-ui package
export type { BaseNodeProps } from '@repo/diagram-ui';

// Memoized wrapper component that integrates with app stores
export const BaseNode = React.memo((props: Parameters<typeof BaseNodeComponent>[0]) => {
  const { id } = props;
  
  // Use optimized selectors to prevent unnecessary re-renders
  const { isRunning } = useNodeExecutionState(id);
  const updateNodeData = useNodeDataUpdater();
  const updateNodeInternals = useUpdateNodeInternals();
  
  return (
    <BaseNodeComponent
      {...props}
      isRunning={isRunning}
      onUpdateData={updateNodeData}
      onUpdateNodeInternals={updateNodeInternals}
      nodeConfigs={getUnifiedNodeConfigsByReactFlowType()}
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
export type { GenericNodeProps } from '@repo/diagram-ui';

// Memoized wrapper for GenericNode that integrates with app stores
export const GenericNode = React.memo((props: Parameters<typeof GenericNodeComponent>[0]) => {
  const { id } = props;
  
  // Use optimized selectors to prevent unnecessary re-renders
  const { isRunning } = useNodeExecutionState(id);
  const updateNodeData = useNodeDataUpdater();
  const updateNodeInternals = useUpdateNodeInternals();
  
  return (
    <GenericNodeComponent
      {...props}
      isRunning={isRunning}
      onUpdateData={updateNodeData}
      onUpdateNodeInternals={updateNodeInternals}
      nodeConfigs={getUnifiedNodeConfigsByReactFlowType()}
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