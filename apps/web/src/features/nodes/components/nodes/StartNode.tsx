import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from '../base/GenericNode';
import { UNIFIED_NODE_CONFIGS } from '@/common/types';

const StartNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const config = UNIFIED_NODE_CONFIGS.start;
  
  if (!config) {
    return null;
  }
  
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
      <span className="text-2xl mb-0.5">{config.emoji}</span>
      <strong className="text-sm">{(data as { label?: string }).label || config.label}</strong>
    </GenericNode>
  );
};

export default StartNode;