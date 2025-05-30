import React from 'react';
import { ContextMenu as ContextMenuBase } from '@repo/diagram-ui';
import { useDiagramContext } from '@/contexts/DiagramContext';

// Re-export types from diagram-ui package
export type { ContextMenuProps } from '@repo/diagram-ui';

// Wrapper component that integrates with app stores and context
export const ContextMenu = React.memo((props: Parameters<typeof ContextMenuBase>[0]) => {
  const { nodeTypes, nodeLabels } = useDiagramContext();
  
  return (
    <ContextMenuBase
      {...props}
      nodeTypes={nodeTypes}
      nodeLabels={nodeLabels}
    />
  );
});

ContextMenu.displayName = 'ContextMenuWrapper';