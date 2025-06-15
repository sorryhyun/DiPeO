import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';

// Main component - memoized for performance
const ConfigurableNode = React.memo<NodeProps>(({ id, type, data, selected }) => {
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
}, (prevProps, nextProps) => {
  // Custom comparison for better performance
  return (
    prevProps.id === nextProps.id &&
    prevProps.type === nextProps.type &&
    prevProps.selected === nextProps.selected &&
    // Deep comparison for data would be expensive, so we check reference
    prevProps.data === nextProps.data
  );
});

ConfigurableNode.displayName = 'ConfigurableNode';

export default ConfigurableNode;