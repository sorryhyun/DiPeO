import React from 'react';
import { BaseNode } from './BaseNode';
import { GenericNodeProps } from '@/shared/types';

function GenericNodeComponent({ 
  id: nodeId,
  data,
  selected,
  nodeType,
  children,
  showFlipButton = true,
  onDragOver,
  onDrop,
  isRunning = false,
  onUpdateData,
  onUpdateNodeInternals,
  nodeConfigs = {}
}: GenericNodeProps) {
  const config = nodeConfigs[nodeType];
  if (!config) {
    console.error(`No configuration found for node type: ${nodeType}`);
    return null;
  }

  return (
    <BaseNode
      id={nodeId}
      selected={selected}
      data={data}
      nodeType={nodeType}
      autoHandles={true}
      showFlipButton={showFlipButton}
      onDragOver={onDragOver}
      onDrop={onDrop}
      isRunning={isRunning}
      onUpdateData={onUpdateData}
      onUpdateNodeInternals={onUpdateNodeInternals}
      nodeConfigs={nodeConfigs}
    >
      {children}
    </BaseNode>
  );
}

// Memoized GenericNode with custom comparison
export const GenericNode = React.memo(GenericNodeComponent, (prevProps, nextProps) => {
  // Only re-render if these specific props change
  return (
    prevProps.id === nextProps.id &&
    prevProps.selected === nextProps.selected &&
    prevProps.isRunning === nextProps.isRunning &&
    prevProps.nodeType === nextProps.nodeType &&
    prevProps.showFlipButton === nextProps.showFlipButton &&
    // Deep compare data object (be careful with large objects)
    JSON.stringify(prevProps.data) === JSON.stringify(nextProps.data) &&
    // Compare children
    prevProps.children === nextProps.children
  );
});

GenericNode.displayName = 'GenericNode';