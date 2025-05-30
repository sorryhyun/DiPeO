import React from 'react';
import { ContextMenu as ContextMenuBase } from '@repo/diagram-ui';
import { useDiagramContext } from '@/shared/contexts/DiagramContext';

// Re-export types from diagram-ui package
export type { ContextMenuProps } from '@repo/diagram-ui';

// Wrapper component that integrates with app stores and context
export const ContextMenu = React.memo((props: Parameters<typeof ContextMenuBase>[0]) => {
  const { nodeTypes, nodeLabels } = useDiagramContext();
  
  // Convert nodeTypes array to Record<string, string> format expected by ContextMenuBase
  const nodeTypesRecord = Object.fromEntries(nodeTypes.map(type => [type, type]));
  
  return (
    <ContextMenuBase
      {...props}
      nodeTypes={nodeTypesRecord}
      nodeLabels={nodeLabels}
    />
  );
});

ContextMenu.displayName = 'ContextMenuWrapper';