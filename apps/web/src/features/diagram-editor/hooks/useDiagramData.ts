import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import type { DomainArrow, DomainNode } from '@/core/types';
import {ArrowID, NodeID} from '@dipeo/domain-models';

interface DiagramData {
  // Maps for efficient lookups
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  
  // Arrays for React Flow and iteration
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  
  // Version for change detection
  dataVersion: number;
}

/**
 * Focused selector hook for diagram data
 * Replaces repetitive useShallow patterns with a single hook
 * 
 * @example
 * ```typescript
 * const { nodes, arrows, nodesArray, arrowsArray } = useDiagramData();
 * ```
 */
export const useDiagramData = (): DiagramData => {
  return useUnifiedStore(
    useShallow(state => ({
      nodes: state.nodes,
      arrows: state.arrows,
      nodesArray: state.nodesArray || Array.from(state.nodes.values()),
      arrowsArray: state.arrowsArray || Array.from(state.arrows.values()),
      dataVersion: state.dataVersion
    }))
  );
};

/**
 * Hook to get a single node by ID
 */
export const useNodeData = (nodeId: NodeID | null): DomainNode | null => {
  return useUnifiedStore(state => nodeId ? state.nodes.get(nodeId) ?? null : null);
};

/**
 * Hook to get a single arrow by ID
 */
export const useArrowData = (arrowId: ArrowID | null): DomainArrow | null => {
  return useUnifiedStore(state => arrowId ? state.arrows.get(arrowId) ?? null : null);
};

/**
 * Hook to get all nodes of a specific type
 */
export const useNodesByType = (type: string): DomainNode[] => {
  return useUnifiedStore(
    useShallow(state => 
      state.nodesArray?.filter(node => node.type === type) || 
      Array.from(state.nodes.values()).filter(node => node.type === type)
    )
  );
};

/**
 * Hook to track diagram changes
 */
export const useDiagramVersion = (): number => {
  return useUnifiedStore(state => state.dataVersion);
};