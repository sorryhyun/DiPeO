import { StateCreator } from 'zustand';
import { DomainArrow, DomainHandle, DomainNode } from '@/core/types';
import { NodeType, NodeExecutionStatus, ArrowID, NodeID, PersonID  } from '@dipeo/domain-models';
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
    totalNodes: number;
    nodesByType: Record<string, number>;
    totalConnections: number;
    unconnectedNodes: number;
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
    
    // Get handles for this node by filtering all handles
    const nodeHandles = Array.from(state.handles.values()).filter(
      handle => handle.nodeId === nodeId
    );
    return nodeHandles.length > 0 ? { ...node, handles: nodeHandles } : node;
  },
  
  getNodesByType: (type) => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => node.type === type);
  },
  
  getNodesByPerson: (personId) => {
    const state = get();
    return Array.from(state.nodes.values()).filter(
      node => node.type === NodeType.PERSON_JOB && node.data.personId === personId
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
    // Filter handles by nodeId
    return Array.from(state.handles.values()).filter(
      handle => handle.nodeId === nodeId
    );
  },
  
  getHandleByName: (nodeId, handleName) => {
    const state = get();
    // Find handle by nodeId and handleName
    return Array.from(state.handles.values()).find(
      h => h.nodeId === nodeId && h.label === handleName
    );
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
    return Array.from(state.nodes.values()).filter(node => node.type === NodeType.START);
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
      node => nodesWithIncoming.has(node.id as NodeID) && !nodesWithOutgoing.has(node.id as NodeID)
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
      const nodeState = state.execution.nodeStates.get(node.id as NodeID);
      return nodeState?.status === NodeExecutionStatus.COMPLETED;
    });
  },
  
  getFailedNodes: () => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => {
      const nodeState = state.execution.nodeStates.get(node.id as NodeID);
      return nodeState?.status === NodeExecutionStatus.FAILED;
    });
  },
  
  // Statistics
  getDiagramStats: () => {
    const state = get();
    const nodesByType: Record<string, number> = {};
    
    state.nodes.forEach(node => {
      nodesByType[node.type] = (nodesByType[node.type] || 0) + 1;
    });
    
    // Find unconnected nodes
    const connectedNodes = new Set<string>();
    state.arrows.forEach(arrow => {
      const sourceNodeId = arrow.source.split(':')[0];
      const targetNodeId = arrow.target.split(':')[0];
      if (sourceNodeId) connectedNodes.add(sourceNodeId);
      if (targetNodeId) connectedNodes.add(targetNodeId);
    });
    
    let unconnectedNodesCount = 0;
    state.nodes.forEach((_node, nodeId) => {
      if (!connectedNodes.has(nodeId)) {
        unconnectedNodesCount++;
      }
    });
    
    return {
      totalNodes: state.nodes.size,
      nodesByType,
      totalConnections: state.arrows.size,
      unconnectedNodes: unconnectedNodesCount
    };
  }
});