import React from 'react';
import { BaseNode } from './BaseNode';
import { GenericNodeProps, UNIFIED_NODE_CONFIGS, getBlockType } from '@/common/types';

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
  nodeConfigs = {},
  ...restProps
}: GenericNodeProps & React.HTMLAttributes<HTMLDivElement>) {
  // Try to get config from provided nodeConfigs first, then fallback to UNIFIED_NODE_CONFIGS
  let config = nodeConfigs[nodeType];
  if (!config) {
    // Convert React Flow type to block type and get config from UNIFIED_NODE_CONFIGS
    const blockType = getBlockType(nodeType);
    config = UNIFIED_NODE_CONFIGS[blockType];
  }
  
  if (!config) {
    console.error(`No configuration found for node type: ${nodeType} (block type: ${getBlockType(nodeType)})`);
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
      {...restProps}
    >
      {children}
    </BaseNode>
  );
}

// Remove memo to allow execution state updates to propagate through
// The BaseNode component handles its own execution state via useNodeExecutionState hook
export const GenericNode = GenericNodeComponent;