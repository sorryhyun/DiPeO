import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';

// Main component - much simpler now
export default function ConfigurableNode({ id, type, data, selected }: NodeProps) {
  // Use the type prop from React Flow directly
  const nodeType = type || 'start';
  
  return (
    <BaseNode
      id={id}
      type={nodeType}
      selected={selected}
      data={data || {}}
    />
  );
}