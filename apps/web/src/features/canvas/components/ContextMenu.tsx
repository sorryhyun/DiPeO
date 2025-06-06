import React from 'react';
import { UNIFIED_NODE_CONFIGS, Node } from '../../../types';

export interface ContextMenuProps {
  position: { x: number; y: number };
  target: 'pane' | 'node' | 'edge';
  selectedNodeId?: string | null;
  selectedArrowId?: string | null;
  containerRef: React.RefObject<HTMLDivElement>;
  onAddNode: (type: Node['type'], position: { x: number; y: number }) => void;
  onAddPerson: () => void;
  onDeleteNode: (nodeId: string) => void;
  onDeleteArrow: (arrowId: string) => void;
  onClose: () => void;
  projectPosition: (x: number, y: number) => { x: number; y: number };
  nodeTypes?: Record<string, string>;
  nodeLabels?: Record<string, string>;
}

const ContextMenu: React.FC<ContextMenuProps> = ({
  position,
  target,
  selectedNodeId,
  selectedArrowId,
  containerRef,
  onAddNode,
  onAddPerson,
  onDeleteNode,
  onDeleteArrow,
  onClose,
  projectPosition,
  nodeTypes: nodeTypesProp,
  nodeLabels: nodeLabelsProp,
}) => {
  // Use props if provided, otherwise derive from UNIFIED_NODE_CONFIGS
  const nodeTypes = nodeTypesProp || Object.keys(UNIFIED_NODE_CONFIGS);
  const nodeLabels = nodeLabelsProp || Object.fromEntries(
    Object.keys(UNIFIED_NODE_CONFIGS).map(key => [key, key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())])
  );
  const handleAddNode = (nodeType: string) => {
    const pos = projectPosition(position.x, position.y);
    onAddNode(nodeType as Node['type'], pos);
    onClose();
  };

  const handleDelete = () => {
    if (target === 'node' && selectedNodeId) {
      onDeleteNode(selectedNodeId);
    } else if (target === 'edge' && selectedArrowId) {
      onDeleteArrow(selectedArrowId);
    }
    onClose();
  };

  const handleAddPerson = () => {
    onAddPerson();
    onClose();
  };

  const containerBounds = containerRef.current?.getBoundingClientRect();
  const menuStyle = {
    top: position.y - (containerBounds?.top ?? 0),
    left: position.x - (containerBounds?.left ?? 0),
  };

  return (
    <div
      className="absolute z-50 bg-white border border-gray-300 rounded shadow-md min-w-48"
      style={menuStyle}
      onClick={(e) => e.stopPropagation()}
    >
      {(target === 'node' || target === 'edge') && (
        <div
          className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-red-600"
          onClick={handleDelete}
        >
          Delete
        </div>
      )}
      
      <div className="border-t border-gray-200">
        <div className="px-4 py-2 text-sm font-medium text-gray-700">Add Block</div>
        {Object.entries(nodeTypes).map(([, nodeType]) => (
          <div
            key={nodeType}
            className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
            onClick={() => handleAddNode(nodeType)}
          >
            {nodeLabels[nodeType] || nodeType}
          </div>
        ))}
      </div>
      
      <div className="border-t border-gray-200">
        <div
          className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
          onClick={handleAddPerson}
        >
          Make LLM Person
        </div>
      </div>
    </div>
  );
};

export default React.memo(ContextMenu);

// Wrapper component for backwards compatibility
export const ContextMenuWrapper = ContextMenu;