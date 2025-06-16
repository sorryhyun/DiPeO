import { StateCreator } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import {
  type NodeID,
  type ArrowID,
  type DomainNode,
  type DomainArrow,
  type NodeKind,
  type Vec2,
  generateNodeId,
  generateArrowId
} from '@/types';
import { UnifiedStore } from '../unifiedStore.types';
import { createNode } from '../helpers/importExportHelpers';
import { updateMap } from '../helpers/entityHelpers';

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
      const updatedArrow = { ...arrow, ...updates };
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
  })
});