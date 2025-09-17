import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';
import TodoNode from './TodoNode';

// Main component - memoized for performance
const ConfigurableNode = React.memo<NodeProps>(({ id, type, data, selected, dragging }) => {
  // Use the type prop from React Flow directly
  const nodeType = type || 'start';

  // Check if this is a TODO-backed note node
  const isTodoNode = nodeType === 'note' && data?.metadata?.isTodoItem;

  if (isTodoNode) {
    return (
      <TodoNode
        id={id}
        type={nodeType}
        data={data || {}}
        selected={selected}
        dragging={dragging}
      />
    );
  }

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
