import React from 'react';
import { BaseNode } from './BaseNode';
import { GenericNodeProps } from '../../../types';
import { NODE_CONFIGS } from '@/config/nodes';
import type { NodeType } from '@/config/nodes';

function GenericNodeComponent({ 
  id: nodeId,
  data,
  selected,
  nodeType,
  children,
  showFlipButton = true,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop,
  isRunning = false,
  onUpdateData,
  onUpdateNodeInternals,
  nodeConfigs = {},
  ...restProps
}: GenericNodeProps & React.HTMLAttributes<HTMLDivElement>) {
  // Try to get config from provided nodeConfigs first, then fallback to NODE_CONFIGS
  let config = nodeConfigs[nodeType];
  if (!config) {
    // Get config from NODE_CONFIGS
    config = NODE_CONFIGS[nodeType as NodeType];
  }
  
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
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
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