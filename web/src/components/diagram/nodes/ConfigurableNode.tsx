import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';
import { isEqual } from 'lodash-es';

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
    // Use deep comparison for data to prevent unnecessary re-renders
    isEqual(prevProps.data, nextProps.data)
  );
});

ConfigurableNode.displayName = 'ConfigurableNode';

export default ConfigurableNode;