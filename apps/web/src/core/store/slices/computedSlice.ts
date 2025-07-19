import { StateCreator } from 'zustand';
import { DomainArrow, DomainHandle, DomainNode, DomainPerson } from '@/core/types';
import { NodeType, NodeExecutionStatus, NodeID, PersonID, Vec2 } from '@dipeo/domain-models';
import { UnifiedStore } from '../unifiedStore.types';
import type { SelectableID } from './uiSlice';
import type { NodeState } from '@/features/execution-monitor/store/executionSlice';
import { ConversionService } from '@/core/services/ConversionService';

export interface ComputedSlice {
  // Array versions of Maps (maintained for React components)
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  personsArray: DomainPerson[];
  handlesArray: DomainHandle[];
  
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
  getSelectedPerson: () => DomainPerson | undefined;
  
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
  
  // Person-related computed getters
  getPersonByLabel: (label: string) => DomainPerson | undefined;
  getPersonsByService: (service: string) => DomainPerson[];
  getUnusedPersons: () => DomainPerson[];
  isPersonInUse: (personId: PersonID) => boolean;
  canDeletePerson: (personId: PersonID) => boolean;
  
  // UI-related computed getters
  isSelected: (id: SelectableID) => boolean;
  getSelectionBounds: () => { min: Vec2; max: Vec2 } | null;
  
  // Execution-related computed getters
  isNodeRunning: (nodeId: NodeID) => boolean;
  getNodeExecutionState: (nodeId: NodeID) => NodeState | undefined;
  getExecutionProgress: () => { completed: number; total: number; percentage: number };
}

export const createComputedSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  ComputedSlice
> = (set, get) => ({
  // Array versions of Maps (initialized as empty)
  nodesArray: [],
  arrowsArray: [],
  personsArray: [],
  handlesArray: [],
  
  // Node-related computed getters
  getNodeWithHandles: (nodeId) => {
    const state = get();
    const node = state.nodes.get(nodeId);
    if (!node) return undefined;
    
    // O(1) lookup using handle index
    const nodeHandles = state.handleIndex.get(nodeId) || [];
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
    // O(1) lookup using handle index
    return state.handleIndex.get(nodeId) || [];
  },
  
  getHandleByName: (nodeId, handleName) => {
    const state = get();
    // O(1) node lookup then O(m) handle search where m is handles per node (typically small)
    const nodeHandles = state.handleIndex.get(nodeId);
    if (!nodeHandles) return undefined;
    return nodeHandles.find(h => h.label === handleName);
  },
  
  // Graph analysis
  getNodeDependencies: (nodeId) => {
    const state = get();
    const dependencies = new Set<NodeID>();
    
    // Find all nodes that this node depends on (incoming connections)
    state.arrows.forEach(arrow => {
      if (arrow.target.includes(nodeId)) {
        const sourceNodeIdStr = arrow.source.split('_')[0];
        if (sourceNodeIdStr) {
          const sourceNodeId = ConversionService.toNodeId(sourceNodeIdStr);
          dependencies.add(sourceNodeId);
        }
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
        const targetNodeIdStr = arrow.target.split('_')[0];
        if (targetNodeIdStr) {
          const targetNodeId = ConversionService.toNodeId(targetNodeIdStr);
          dependents.add(targetNodeId);
        }
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
      const sourceNodeIdStr = arrow.source.split('_')[0];
      const targetNodeIdStr = arrow.target.split('_')[0];
      if (sourceNodeIdStr) {
        nodesWithOutgoing.add(ConversionService.toNodeId(sourceNodeIdStr));
      }
      if (targetNodeIdStr) {
        nodesWithIncoming.add(ConversionService.toNodeId(targetNodeIdStr));
      }
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
      return state.nodes.get(ConversionService.toNodeId(state.selectedId));
    }
    return undefined;
  },
  
  getSelectedArrow: () => {
    const state = get();
    if (state.selectedType === 'arrow' && state.selectedId) {
      return state.arrows.get(ConversionService.toArrowId(state.selectedId));
    }
    return undefined;
  },
  
  getSelectedPerson: () => {
    const state = get();
    if (state.selectedType === 'person' && state.selectedId) {
      return state.persons.get(ConversionService.toPersonId(state.selectedId));
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
      return nodeState?.status === NodeExecutionStatus.COMPLETED;
    });
  },
  
  getFailedNodes: () => {
    const state = get();
    return Array.from(state.nodes.values()).filter(node => {
      const nodeState = state.execution.nodeStates.get(node.id);
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
      const sourceNodeId = arrow.source.split('_')[0];
      const targetNodeId = arrow.target.split('_')[0];
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
  },
  
  // Person-related computed getters
  getPersonByLabel: (label) => {
    const state = get();
    return Array.from(state.persons.values()).find(
      person => person.label === label
    );
  },
  
  getPersonsByService: (service) => {
    const state = get();
    return Array.from(state.persons.values()).filter(
      person => person.llm_config?.service === service
    );
  },
  
  getUnusedPersons: () => {
    const state = get();
    const usedPersonIds = new Set<PersonID>();
    
    state.nodes.forEach(node => {
      if ((node.type === NodeType.PERSON_JOB || node.type === NodeType.PERSON_BATCH_JOB) && node.data.person_id) {
        usedPersonIds.add(node.data.person_id);
      }
    });
    
    return Array.from(state.persons.values()).filter(
      person => !usedPersonIds.has(person.id as PersonID)
    );
  },
  
  isPersonInUse: (personId) => {
    const state = get();
    return Array.from(state.nodes.values()).some(
      node => (node.type === NodeType.PERSON_JOB || node.type === NodeType.PERSON_BATCH_JOB) && node.data.person_id === personId
    );
  },
  
  canDeletePerson: (personId) => {
    const state = get();
    return !Array.from(state.nodes.values()).some(
      node => (node.type === NodeType.PERSON_JOB || node.type === NodeType.PERSON_BATCH_JOB) && node.data.person_id === personId
    );
  },
  
  // UI-related computed getters
  isSelected: (id) => {
    const state = get();
    return state.selectedId === id || state.multiSelectedIds.has(id);
  },
  
  getSelectionBounds: () => {
    const state = get();
    const selectedIds = state.multiSelectedIds.size > 0 
      ? Array.from(state.multiSelectedIds)
      : state.selectedId ? [state.selectedId] : [];
    
    if (selectedIds.length === 0) return null;
    
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    selectedIds.forEach(id => {
      const node = state.nodes.get(id as NodeID);
      if (node) {
        minX = Math.min(minX, node.position.x);
        minY = Math.min(minY, node.position.y);
        maxX = Math.max(maxX, node.position.x + 200); // Assume node width
        maxY = Math.max(maxY, node.position.y + 100); // Assume node height
      }
    });
    
    return {
      min: { x: minX, y: minY },
      max: { x: maxX, y: maxY }
    };
  },
  
  // Execution-related computed getters
  isNodeRunning: (nodeId) => {
    const state = get();
    return state.execution.runningNodes.has(nodeId);
  },
  
  getNodeExecutionState: (nodeId) => {
    const state = get();
    return state.execution.nodeStates.get(nodeId);
  },
  
  getExecutionProgress: () => {
    const state = get();
    const total = state.nodes.size;
    const completed = Array.from(state.execution.nodeStates.values())
      .filter(nodeState => 
        nodeState.status === NodeExecutionStatus.COMPLETED || 
        nodeState.status === NodeExecutionStatus.SKIPPED ||
        nodeState.status === NodeExecutionStatus.FAILED
      ).length;
    
    return {
      completed,
      total,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0
    };
  }
});