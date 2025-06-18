import { StateCreator } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { ArrowID, DomainArrow, DomainNode, NodeID, Vec2 } from '@/core/types';
import { NodeKind } from '@/features/diagram-editor/types/node-kinds';
import { NodeType } from '@dipeo/domain-models';
import { generateNodeId, generateArrowId } from '@/core/types/utilities';
import { UnifiedStore } from '@/core/store/unifiedStore.types';
import { createNode } from '@/core/store/helpers/importExportHelpers';
import { updateMap } from '@/core/store/helpers/entityHelpers';

export interface DiagramSlice {
  // Core data structures
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  
  // Maintain arrays for stable references
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  
  // Data version for tracking changes
  dataVersion: number;
  
  // Node operations
  addNode: (type: NodeKind, position: Vec2, initialData?: any) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  updateNodeSilently: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  
  // Arrow operations
  addArrow: (source: string, target: string, data?: any) => ArrowID;
  updateArrow: (id: ArrowID, updates: Partial<DomainArrow>) => void;
  deleteArrow: (id: ArrowID) => void;
  
  // Batch operations
  batchUpdateNodes: (updates: Array<{id: NodeID, updates: Partial<DomainNode>}>) => void;
  batchDeleteNodes: (ids: NodeID[]) => void;
  
  // Utility
  clearDiagram: () => void;
  validateDiagram: () => { isValid: boolean; errors: string[] };
}

export const createDiagramSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  DiagramSlice
> = (set, get) => ({
  // Initialize data structures
  nodes: new Map(),
  arrows: new Map(),
  nodesArray: [],
  arrowsArray: [],
  dataVersion: 0,
  
  // Node operations with array sync
  addNode: (type, position, initialData) => {
    const node = createNode(type, position, initialData);
    set(state => {
      state.nodes.set(node.id as NodeID, node);
      state.nodesArray = Array.from(state.nodes.values());
      state.dataVersion += 1;
    });
    return node.id as NodeID;
  },
  
  updateNode: (id, updates) => set(state => {
    const node = state.nodes.get(id);
    if (node) {
      const updatedNode = { ...node, ...updates };
      state.nodes.set(id, updatedNode);
      state.nodesArray = Array.from(state.nodes.values());
      state.dataVersion += 1;
    }
  }),
  
  updateNodeSilently: (id, updates) => set(state => {
    const node = state.nodes.get(id);
    if (node) {
      const updatedNode = { ...node, ...updates };
      state.nodes.set(id, updatedNode);
      state.nodesArray = Array.from(state.nodes.values());
      // No version increment for silent updates
    }
  }),
  
  deleteNode: (id) => set(state => {
    const deleted = state.nodes.delete(id);
    if (deleted) {
      // Remove connected arrows
      const arrowsToDelete = Array.from(state.arrows.entries())
        .filter(([_, arrow]) => 
          arrow.source.includes(id) || arrow.target.includes(id)
        )
        .map(([arrowId]) => arrowId);
      
      arrowsToDelete.forEach(arrowId => state.arrows.delete(arrowId));
      
      state.nodesArray = Array.from(state.nodes.values());
      state.arrowsArray = Array.from(state.arrows.values());
      state.dataVersion += 1;
    }
  }),
  
  // Arrow operations with array sync
  addArrow: (source, target, data) => {
    const arrow: DomainArrow = {
      id: generateArrowId(),
      source,
      target,
      data: data || {}
    };
    set(state => {
      state.arrows.set(arrow.id as ArrowID, arrow);
      state.arrowsArray = Array.from(state.arrows.values());
      state.dataVersion += 1;
    });
    return arrow.id as ArrowID;
  },
  
  updateArrow: (id, updates) => set(state => {
    const arrow = state.arrows.get(id);
    if (arrow) {
      // Special handling for data property to merge instead of replace
      const updatedArrow = { ...arrow, ...updates };
      if (updates.data && arrow.data) {
        updatedArrow.data = { ...arrow.data, ...updates.data };
      }
      state.arrows.set(id, updatedArrow);
      state.arrowsArray = Array.from(state.arrows.values());
      state.dataVersion += 1;
    }
  }),
  
  deleteArrow: (id) => set(state => {
    const deleted = state.arrows.delete(id);
    if (deleted) {
      state.arrowsArray = Array.from(state.arrows.values());
      state.dataVersion += 1;
    }
  }),
  
  // Batch operations for performance
  batchUpdateNodes: (updates) => set(state => {
    let hasChanges = false;
    updates.forEach(({ id, updates: nodeUpdates }) => {
      const node = state.nodes.get(id);
      if (node) {
        state.nodes.set(id, { ...node, ...nodeUpdates });
        hasChanges = true;
      }
    });
    
    if (hasChanges) {
      state.nodesArray = Array.from(state.nodes.values());
      state.dataVersion += 1;
    }
  }),
  
  batchDeleteNodes: (ids) => set(state => {
    let hasChanges = false;
    ids.forEach(id => {
      if (state.nodes.delete(id)) {
        hasChanges = true;
        
        // Remove connected arrows
        const arrowsToDelete = Array.from(state.arrows.entries())
          .filter(([_, arrow]) => 
            arrow.source.includes(id) || arrow.target.includes(id)
          )
          .map(([arrowId]) => arrowId);
        
        arrowsToDelete.forEach(arrowId => state.arrows.delete(arrowId));
      }
    });
    
    if (hasChanges) {
      state.nodesArray = Array.from(state.nodes.values());
      state.arrowsArray = Array.from(state.arrows.values());
      state.dataVersion += 1;
    }
  }),
  
  clearDiagram: () => set(state => {
    state.nodes.clear();
    state.arrows.clear();
    state.nodesArray = [];
    state.arrowsArray = [];
    state.dataVersion += 1;
  }),

  validateDiagram: () => {
    const state = get();
    const errors: string[] = [];
    
    // Check for empty diagram
    if (state.nodes.size === 0) {
      errors.push('Diagram has no nodes');
      return { isValid: false, errors };
    }
    
    // Check for start node
    const hasStartNode = Array.from(state.nodes.values()).some(
      node => node.type === NodeType.START
    );
    if (!hasStartNode) {
      errors.push('Diagram must have at least one start node');
    }
    
    // Check for endpoint node
    const hasEndpoint = Array.from(state.nodes.values()).some(
      node => node.type === NodeType.ENDPOINT
    );
    if (!hasEndpoint) {
      errors.push('Diagram should have at least one endpoint node');
    }
    
    // Check for unconnected nodes
    const connectedNodes = new Set<string>();
    state.arrows.forEach(arrow => {
      const sourceNodeId = arrow.source.split(':')[0];
      const targetNodeId = arrow.target.split(':')[0];
      if (sourceNodeId) connectedNodes.add(sourceNodeId);
      if (targetNodeId) connectedNodes.add(targetNodeId);
    });
    
    const unconnectedNodes = Array.from(state.nodes.values()).filter(
      node => !connectedNodes.has(node.id) && node.type !== NodeType.START
    );
    
    if (unconnectedNodes.length > 0) {
      errors.push(`${unconnectedNodes.length} node(s) are not connected`);
    }
    
    // Check for person nodes without assigned persons
    state.nodes.forEach(node => {
      if ((node.type === NodeType.PERSON_JOB || node.type === NodeType.PERSON_BATCH_JOB) && !node.data?.person) {
        errors.push(`Node ${node.displayName || node.id} requires a person to be assigned`);
      }
    });
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
});