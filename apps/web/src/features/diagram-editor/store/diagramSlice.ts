import { StateCreator } from 'zustand';
import { ArrowID, DomainArrow, DomainNode, NodeID, HandleID } from '@/core/types';
import { generateArrowId } from '@/core/types/utilities';
import { UnifiedStore } from '@/core/store/unifiedStore.types';
import { createNode } from '@/core/store/helpers/importExportHelpers';
import { recordHistory } from '@/core/store/helpers/entityHelpers';
import { NodeType, Vec2 } from '@dipeo/domain-models';
import { ContentType } from '@/__generated__/graphql';

export interface DiagramSlice {
  // Core data structures
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  
  // Array getters for React components
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  
  // Data version for tracking changes
  dataVersion: number;
  
  // Diagram metadata
  diagramName: string;
  diagramId: string | null;
  
  // Node operations
  addNode: (type: NodeType, position: Vec2, initialData?: Record<string, unknown>) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  updateNodeSilently: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  getNode: (id: NodeID) => DomainNode | undefined;
  
  // Arrow operations
  addArrow: (source: string, target: string, data?: Record<string, unknown>) => ArrowID;
  updateArrow: (id: ArrowID, updates: Partial<DomainArrow>) => void;
  deleteArrow: (id: ArrowID) => void;
  getArrow: (id: ArrowID) => DomainArrow | undefined;
  
  // Batch operations
  batchUpdateNodes: (updates: Array<{id: NodeID, updates: Partial<DomainNode>}>) => void;
  batchDeleteNodes: (ids: NodeID[]) => void;
  
  // Diagram metadata operations
  setDiagramName: (name: string) => void;
  setDiagramId: (id: string | null) => void;
  
  // Utility
  clearDiagram: () => void;
  validateDiagram: () => { isValid: boolean; errors: string[] };
}

// Helper function to sync arrays with maps
const syncArrays = (state: UnifiedStore) => {
  state.nodesArray = Array.from(state.nodes.values());
  state.arrowsArray = Array.from(state.arrows.values());
};

// Helper to handle post-change operations
const afterChange = (state: UnifiedStore) => {
  state.dataVersion += 1;
  syncArrays(state);
  recordHistory(state);
};

export const createDiagramSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  DiagramSlice
> = (set, get) => ({
  // Initialize data structures
  nodes: new Map(),
  arrows: new Map(),
  dataVersion: 0,
  nodesArray: [],
  arrowsArray: [],
  diagramName: 'Untitled',
  diagramId: null,

  // Node operations
  addNode: (type, position, initialData) => {
    const node = createNode(type, position, initialData);
    set(state => {
      state.nodes.set(node.id as NodeID, node);
      afterChange(state);
    });
    return node.id as NodeID;
  },

  updateNode: (id, updates) => {
    set(state => {
      const node = state.nodes.get(id);
      if (node) {
        const updatedNode = { ...node, ...updates };
        state.nodes.set(id, updatedNode);
        afterChange(state);
      }
    });
  },
  
  updateNodeSilently: (id, updates) => {
    set(state => {
      const node = state.nodes.get(id);
      if (node) {
        const updatedNode = { ...node, ...updates };
        state.nodes.set(id, updatedNode);
        syncArrays(state);
        // No version increment or history for silent updates
      }
    });
  },
  
  deleteNode: (id) => {
    set(state => {
      const deleted = state.nodes.delete(id);
      if (deleted) {
        // Remove connected arrows
        const arrowsToDelete = Array.from(state.arrows.entries())
          .filter(([_, arrow]) => {
            const sourceNodeId = (arrow.source as string).split(':')[0];
            const targetNodeId = (arrow.target as string).split(':')[0];
            return sourceNodeId === id || targetNodeId === id;
          })
          .map(([arrowId]) => arrowId);
        
        arrowsToDelete.forEach(arrowId => state.arrows.delete(arrowId));
        
        // Clear selection if deleted
        if (state.selectedId === id) {
          state.selectedId = null;
          state.selectedType = null;
        }
        
        afterChange(state);
      }
    });
  },

  getNode: (id) => get().nodes.get(id),
  
  // Arrow operations
  addArrow: (source, target, data) => {
    // Extract content_type and label from data if present
    let content_type: ContentType | undefined;
    let label: string | undefined;
    let arrowData = data;
    
    if (data) {
      const { content_type: ct, label: l, ...restData } = data;
      content_type = ct as ContentType | undefined;
      label = l as string | undefined;
      arrowData = Object.keys(restData).length > 0 ? restData : undefined;
    }
    
    const arrow: DomainArrow = {
      id: generateArrowId(),
      source: source as HandleID,
      target: target as HandleID,
      data: arrowData  // DomainArrow.data is optional
    };
    
    // Add optional fields only if they have actual values
    if (content_type !== undefined && content_type !== null) {
      arrow.content_type = content_type;
    }
    if (label !== undefined && label !== null) {
      arrow.label = label;
    }
    
    set(state => {
      // Validate source and target nodes exist
      const sourceNodeId = source.split(':')[0];
      const targetNodeId = target.split(':')[0];
      if (!state.nodes.has(sourceNodeId as NodeID)) {
        throw new Error(`Source node ${sourceNodeId} not found`);
      }
      if (!state.nodes.has(targetNodeId as NodeID)) {
        throw new Error(`Target node ${targetNodeId} not found`);
      }
      
      state.arrows.set(arrow.id as ArrowID, arrow);
      afterChange(state);
    });
    
    return arrow.id as ArrowID;
  },

  updateArrow: (id, updates) => {
    set(state => {
      const arrow = state.arrows.get(id);
      if (arrow) {
        // Special handling for data property to merge instead of replace
        const updatedArrow = { ...arrow, ...updates };
        if (updates.data && arrow.data) {
          updatedArrow.data = { ...arrow.data, ...updates.data };
        }
        state.arrows.set(id, updatedArrow);
        afterChange(state);
      }
    });
  },

  deleteArrow: (id) => {
    set(state => {
      const deleted = state.arrows.delete(id);
      if (deleted) {
        afterChange(state);
      }
    });
  },

  getArrow: (id) => get().arrows.get(id),

  // Batch operations for performance
  batchUpdateNodes: (updates) => {
    set(state => {
      let hasChanges = false;
      updates.forEach(({ id, updates: nodeUpdates }) => {
        const node = state.nodes.get(id);
        if (node) {
          state.nodes.set(id, { ...node, ...nodeUpdates });
          hasChanges = true;
        }
      });
      
      if (hasChanges) {
        afterChange(state);
      }
    });
  },
  
  batchDeleteNodes: (ids) => {
    set(state => {
      let hasChanges = false;
      ids.forEach(id => {
        if (state.nodes.delete(id)) {
          hasChanges = true;
          
          // Remove connected arrows
          const arrowsToDelete = Array.from(state.arrows.entries())
            .filter(([_, arrow]) => {
              const sourceNodeId = (arrow.source as string).split(':')[0];
              const targetNodeId = (arrow.target as string).split(':')[0];
              return sourceNodeId === id || targetNodeId === id;
            })
            .map(([arrowId]) => arrowId);
          
          arrowsToDelete.forEach(arrowId => state.arrows.delete(arrowId));
          
          // Clear selection if deleted
          if (state.selectedId === id) {
            state.selectedId = null;
            state.selectedType = null;
          }
        }
      });
      
      if (hasChanges) {
        afterChange(state);
      }
    });
  },
  
  // Diagram metadata operations
  setDiagramName: (name) => {
    set(state => {
      state.diagramName = name;
      // Don't increment version or record history for metadata changes
    });
  },
  
  setDiagramId: (id) => {
    set(state => {
      state.diagramId = id;
      // Don't increment version or record history for metadata changes
    });
  },
  
  clearDiagram: () => {
    set(state => {
      state.nodes.clear();
      state.arrows.clear();
      afterChange(state);
    });
  },

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
        errors.push(`Node ${node.data?.label || node.id} requires a person to be assigned`);
      }
    });
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
});