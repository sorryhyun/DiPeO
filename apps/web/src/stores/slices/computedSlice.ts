import { StateCreator } from 'zustand';
import {
  type NodeID,
  type ArrowID,
  type DomainNode,
  type DomainArrow,
  type DomainHandle,
  type PersonID
} from '@/types';
import { UnifiedStore } from '../unifiedStore.types';

export interface ComputedSlice {
  // Node-related computed getters
  getNodeWithHandles: (nodeId: NodeID) => (DomainNode & { handles?: DomainHandle[] }) | undefined;
  getNodesByType: (type: string) => DomainNode[];
  getNodesByPerson: (personId: PersonID) => DomainNode[];
  
  // Arrow-related computed getters
  getConnectedArrows: (nodeId: NodeID) => DomainArrow[];
  getOutgoingArrows: (nodeId: NodeID) => DomainArrow[];
  getIncomingArrows: (nodeId: NodeID) => DomainArrow[];
  getArrowsBetween: (sourceId: NodeID, targetId: NodeID) => DomainArrow[];
  
  // Handle-related computed getters
  getNodeHandles: (nodeId: NodeID) => DomainHandle[] | undefined;
  getHandleByName: (nodeId: NodeID, handleName: string) => DomainHandle | undefined;
  
  // Graph analysis
  getNodeDependencies: (nodeId: NodeID) => Set<NodeID>;
  getNodeDependents: (nodeId: NodeID) => Set<NodeID>;
  getStartNodes: () => DomainNode[];
  getEndNodes: () => DomainNode[];
  
  // Selection helpers
  getSelectedNode: () => DomainNode | undefined;
  getSelectedArrow: () => DomainArrow | undefined;
  getSelectedPerson: () => any | undefined;
  
  // Execution state helpers
  getRunningNodes: () => DomainNode[];
  getCompletedNodes: () => DomainNode[];
  getFailedNodes: () => DomainNode[];
  
  // Statistics
  getDiagramStats: () => {
    nodeCount: number;
    arrowCount: number;
    personCount: number;
    nodesByType: Record<string, number>;
  };
}

export const createComputedSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  ComputedSlice
> = (set, get) => ({
  // Node-related computed getters
  getNodeWithHandles: (nodeId) => {
    const state = get();
    const node = state.nodes.get(nodeId);
    if (!node) return undefined;
    
    const handles = state.handles.get(nodeId);
    return handles ? { ...node, handles } : node;
  },
  
  getNodesByType: (type) => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => node.type === type);
  },
  
  getNodesByPerson: (personId) => {
    const state = get();
    return Array.from(state.nodes.values()).filter(
      node => node.type === 'person_job' && node.data.personId === personId
    );
  },
  
  // Arrow-related computed getters
  getConnectedArrows: (nodeId) => {
    const state = get();
    return Array.from(state.arrows.values()).filter(
      arrow => arrow.source.includes(nodeId) || arrow.target.includes(nodeId)
    );
  },
  
  getOutgoingArrows: (nodeId) => {
    const state = get();
    return Array.from(state.arrows.values()).filter(
      arrow => arrow.source.includes(nodeId)
    );
  },
  
  getIncomingArrows: (nodeId) => {
    const state = get();
    return Array.from(state.arrows.values()).filter(
      arrow => arrow.target.includes(nodeId)
    );
  },
  
  getArrowsBetween: (sourceId, targetId) => {
    const state = get();
    return Array.from(state.arrows.values()).filter(
      arrow => arrow.source.includes(sourceId) && arrow.target.includes(targetId)
    );
  },
  
  // Handle-related computed getters
  getNodeHandles: (nodeId) => {
    const state = get();
    return state.handles.get(nodeId);
  },
  
  getHandleByName: (nodeId, handleName) => {
    const state = get();
    const handles = state.handles.get(nodeId);
    return handles?.find(h => h.name === handleName);
  },
  
  // Graph analysis
  getNodeDependencies: (nodeId) => {
    const state = get();
    const dependencies = new Set<NodeID>();
    
    // Find all nodes that this node depends on (incoming connections)
    state.arrows.forEach(arrow => {
      if (arrow.target.includes(nodeId)) {
        const sourceNodeId = arrow.source.split(':')[0] as NodeID;
        dependencies.add(sourceNodeId);
      }
    });
    
    return dependencies;
  },
  
  getNodeDependents: (nodeId) => {
    const state = get();
    const dependents = new Set<NodeID>();
    
    // Find all nodes that depend on this node (outgoing connections)
    state.arrows.forEach(arrow => {
      if (arrow.source.includes(nodeId)) {
        const targetNodeId = arrow.target.split(':')[0] as NodeID;
        dependents.add(targetNodeId);
      }
    });
    
    return dependents;
  },
  
  getStartNodes: () => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => node.type === 'start');
  },
  
  getEndNodes: () => {
    const state = get();
    const nodesWithOutgoing = new Set<NodeID>();
    const nodesWithIncoming = new Set<NodeID>();
    
    state.arrows.forEach(arrow => {
      nodesWithOutgoing.add(arrow.source.split(':')[0] as NodeID);
      nodesWithIncoming.add(arrow.target.split(':')[0] as NodeID);
    });
    
    // End nodes are nodes with incoming connections but no outgoing connections
    return Array.from(state.nodes.values()).filter(
      node => nodesWithIncoming.has(node.id) && !nodesWithOutgoing.has(node.id)
    );
  },
  
  // Selection helpers
  getSelectedNode: () => {
    const state = get();
    if (state.selectedType === 'node' && state.selectedId) {
      return state.nodes.get(state.selectedId as NodeID);
    }
    return undefined;
  },
  
  getSelectedArrow: () => {
    const state = get();
    if (state.selectedType === 'arrow' && state.selectedId) {
      return state.arrows.get(state.selectedId as ArrowID);
    }
    return undefined;
  },
  
  getSelectedPerson: () => {
    const state = get();
    if (state.selectedType === 'person' && state.selectedId) {
      return state.persons.get(state.selectedId as PersonID);
    }
    return undefined;
  },
  
  // Execution state helpers
  getRunningNodes: () => {
    const state = get();
    return Array.from(state.execution.runningNodes)
      .map(nodeId => state.nodes.get(nodeId))
      .filter((node): node is DomainNode => node !== undefined);
  },
  
  getCompletedNodes: () => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => {
      const nodeState = state.execution.nodeStates.get(node.id);
      return nodeState?.status === 'completed';
    });
  },
  
  getFailedNodes: () => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => {
      const nodeState = state.execution.nodeStates.get(node.id);
      return nodeState?.status === 'failed';
    });
  },
  
  // Statistics
  getDiagramStats: () => {
    const state = get();
    const nodesByType: Record<string, number> = {};
    
    state.nodes.forEach(node => {
      nodesByType[node.type] = (nodesByType[node.type] || 0) + 1;
    });
    
    return {
      nodeCount: state.nodes.size,
      arrowCount: state.arrows.size,
      personCount: state.persons.size,
      nodesByType
    };
  }
});