import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';

// Main component - memoized for performance
const ConfigurableNode = React.memo<NodeProps>(({ id, type, data, selected, dragging }) => {
  // Use the type prop from React Flow directly
  const nodeType = type || 'start';

  return (
    <BaseNode
      id={id}
      type={nodeType}
      selected={selected}
      data={data || {}}
      dragging={dragging}
    />
  );
});

ConfigurableNode.displayName = 'ConfigurableNode';

export default ConfigurableNode;
