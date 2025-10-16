import React from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';
import TodoNode from './TodoNode';

// Main component - memoized for performance
const ConfigurableNode = React.memo<NodeProps>((props) => {
  // Use the type prop from React Flow directly
  const nodeType = props.type || 'start';

  // Check if this is a TODO-backed note node
  const metadata = (props.data as Record<string, unknown>)?.metadata as Record<string, unknown> | undefined;
  const isTodoNode = nodeType === 'note' && metadata?.isTodoItem;

  if (isTodoNode) {
    // Pass through all props to TodoNode
    return <TodoNode {...props} />;
  }

  return (
    <BaseNode
      id={props.id}
      type={nodeType}
      selected={props.selected}
      data={props.data || {}}
      dragging={props.dragging}
    />
  );
});

ConfigurableNode.displayName = 'ConfigurableNode';

export default ConfigurableNode;
