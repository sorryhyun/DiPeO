import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './base/BaseNode';

// Main component - much simpler now
export default function ConfigurableNode({ id, data, selected }: NodeProps) {
  const nodeType = data?.type || 'start';
  
  return (
    <BaseNode
      id={id}
      type={nodeType}
      selected={selected}
      data={data || {}}
    />
  );
}