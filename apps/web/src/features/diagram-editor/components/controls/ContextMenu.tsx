import React, { useMemo, useCallback } from 'react';
import { DomainNode } from '@/core/types';
import {ArrowID, NodeID} from '@dipeo/domain-models';
import { UNIFIED_NODE_CONFIGS } from '@/core/config';
import { useCanvasOperationsContext, useCanvasSelection } from '@/shared/contexts/CanvasContext';
import { useUnifiedStore } from '@/core/store/unifiedStore';

export interface ContextMenuProps {
  position: { x: number; y: number };
  target: 'pane' | 'node' | 'edge';
  containerRef: React.RefObject<HTMLDivElement>;
  onClose: () => void;
  projectPosition: (x: number, y: number) => { x: number; y: number };
  nodeTypes?: Record<string, string>;
  nodeLabels?: Record<string, string>;
}

// Pre-compute default node types and labels at module level
const DEFAULT_NODE_TYPES = Object.keys(UNIFIED_NODE_CONFIGS);
const DEFAULT_NODE_LABELS = Object.fromEntries(
  DEFAULT_NODE_TYPES.map(key => [
    key, 
    key.replace(/_/g, ' ').replace(/\b\w/g, l => l)
  ])
);

const ContextMenu: React.FC<ContextMenuProps> = ({
  position,
  target,
  containerRef,
  onClose,
  projectPosition,
  nodeTypes: nodeTypesProp,
  nodeLabels: nodeLabelsProp,
}) => {
  // Get operations and selection from context
  const { nodeOps, arrowOps } = useCanvasOperationsContext();
  const { selectedNodeId, selectedArrowId } = useCanvasSelection();
  // Use props if provided, otherwise use pre-computed defaults
  const nodeTypes = nodeTypesProp || DEFAULT_NODE_TYPES;
  const nodeLabels = nodeLabelsProp || DEFAULT_NODE_LABELS;
  
  // Memoize node entries to avoid re-creating on every render
  const nodeEntries = useMemo(() => {
    return Array.isArray(nodeTypes) 
      ? nodeTypes.map(type => [type, type])
      : Object.entries(nodeTypes);
  }, [nodeTypes]);
  
  const handleAddNode = useCallback((nodeType: string) => {
    const pos = projectPosition(position.x, position.y);
    nodeOps.addNode(nodeType as DomainNode['type'], pos);
    onClose();
  }, [position.x, position.y, projectPosition, nodeOps, onClose]);

  const handleDelete = useCallback(() => {
    if (target === 'node' && selectedNodeId) {
      nodeOps.deleteNode(selectedNodeId);
    } else if (target === 'edge' && selectedArrowId) {
      arrowOps.deleteArrow(selectedArrowId);
    }
    onClose();
  }, [target, selectedNodeId, selectedArrowId, nodeOps, arrowOps, onClose]);

  const handleAddPerson = useCallback(() => {
    // Open modal instead of directly adding - let the modal handle the details
    const openPersonModal = useUnifiedStore.getState().openModal;
    openPersonModal('person');
    onClose();
  }, [onClose]);

  // Memoize menu style calculation
  const menuStyle = useMemo(() => {
    const containerBounds = containerRef.current?.getBoundingClientRect();
    return {
      top: position.y - (containerBounds?.top ?? 0),
      left: position.x - (containerBounds?.left ?? 0),
    };
  }, [position.x, position.y, containerRef]);

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
        {nodeEntries.map(([, nodeType]) => (
          <div
            key={nodeType}
            className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
            onClick={() => handleAddNode(nodeType as string)}
          >
            {nodeLabels[nodeType as string] || nodeType}
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