import { StateCreator } from 'zustand';
import { ArrowID, DomainArrow, DomainNode, NodeID, HandleID } from '@/core/types';
import { generateArrowId } from '@/core/types/utilities';
import { ConversionService } from '@/core/services/ConversionService';
import { UnifiedStore } from '@/core/store/unifiedStore.types';
import { createNode } from '@/core/store/helpers/importExportHelpers';
import { getNodeConfig } from '../config/nodes';
import { recordHistory } from '@/core/store/helpers/entityHelpers';
import { NodeType, Vec2, DiagramFormat } from '@dipeo/domain-models';

export interface DiagramSlice {
  // Core data structures
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  
  // Data version for tracking changes
  dataVersion: number;
  
  // Diagram metadata
  diagramName: string;
  diagramDescription: string;
  diagramId: string | null;
  diagramFormat: DiagramFormat | null;
  
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
  setDiagramDescription: (description: string) => void;
  setDiagramId: (id: string | null) => void;
  setDiagramFormat: (format: DiagramFormat | null) => void;
  
  // Utility
  clearDiagram: () => void;
  restoreDiagram: (nodes: Map<NodeID, DomainNode>, arrows: Map<ArrowID, DomainArrow>) => void;
  restoreDiagramSilently: (nodes: Map<NodeID, DomainNode>, arrows: Map<ArrowID, DomainArrow>) => void;
  triggerArraySync: () => void;
  validateDiagram: () => { isValid: boolean; errors: string[] };
}


// Helper to handle post-change operations
const afterChange = (state: UnifiedStore) => {
  state.dataVersion += 1;
  // Arrays are now synced via middleware to avoid cross-slice violations
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
  diagramName: 'Untitled',
  diagramDescription: '',
  diagramId: null,
  diagramFormat: null,

  // Node operations
  addNode: (type, position, initialData) => {
    const nodeConfig = getNodeConfig(type);
    const nodeDefaults = nodeConfig ? { ...nodeConfig.defaults } : {};
    const mergedData = { ...nodeDefaults, ...initialData };
    const node = createNode(type, position, mergedData);
    set(state => {
      state.nodes.set(ConversionService.toNodeId(node.id), node);
      afterChange(state);
    });
    return ConversionService.toNodeId(node.id);
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
        // No version increment or history for silent updates
        // Arrays will be recomputed automatically when accessed
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
            const sourceNodeId = ConversionService.parseHandleId(arrow.source).node_id;
            const targetNodeId = ConversionService.parseHandleId(arrow.target).node_id;
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
    
    // Call the unified store's handle cleanup method
    get().cleanupNodeHandles(id);
  },

  getNode: (id) => get().nodes.get(id),
  
  // Arrow operations
  addArrow: (source, target, data) => {
    // Extract content_type and label from data if present
    let content_type: string | undefined;
    let label: string | undefined;
    let arrowData = data;
    
    if (data) {
      const { content_type: ct, label: l, ...restData } = data;
      content_type = typeof ct === 'string' ? ct : undefined;
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
      (arrow as any).content_type = content_type;
    }
    if (label !== undefined && label !== null) {
      arrow.label = label;
    }
    
    set(state => {
      // Validate source and target nodes exist

      let sourceNodeId: NodeID;
      let targetNodeId: NodeID;
      
      try {
        const sourceParsed = ConversionService.parseHandleId(ConversionService.toHandleId(source));
        const targetParsed = ConversionService.parseHandleId(ConversionService.toHandleId(target));
        sourceNodeId = sourceParsed.node_id;
        targetNodeId = targetParsed.node_id;
      } catch (e) {
        console.error('Failed to parse handle IDs:', e);
        throw new Error(`Invalid handle ID format: ${source} or ${target}`);
      }
      
      if (!state.nodes.has(sourceNodeId)) {
        console.error('Available nodes:', Array.from(state.nodes.keys()));
        throw new Error(`Source node ${sourceNodeId} not found`);
      }
      if (!state.nodes.has(targetNodeId)) {
        throw new Error(`Target node ${targetNodeId} not found`);
      }
      
      state.arrows.set(ConversionService.toArrowId(arrow.id), arrow);
      afterChange(state);
    });
    
    return ConversionService.toArrowId(arrow.id);
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
              const sourceNodeId = ConversionService.parseHandleId(arrow.source).node_id;
              const targetNodeId = ConversionService.parseHandleId(arrow.target).node_id;
              return sourceNodeId === id || targetNodeId === id;
            })
            .map(([arrowId]) => arrowId);
          
          arrowsToDelete.forEach(arrowId => state.arrows.delete(arrowId));
        }
      });
      
      if (hasChanges) {
        afterChange(state);
      }
    });
    
    // Clean up handles for all deleted nodes
    ids.forEach(id => get().cleanupNodeHandles(id));
  },
  
  // Diagram metadata operations
  setDiagramName: (name) => {
    set(state => {
      state.diagramName = name;
      // Don't increment version or record history for metadata changes
    });
  },
  
  setDiagramDescription: (description) => {
    set(state => {
      state.diagramDescription = description;
      // Don't increment version or record history for metadata changes
    });
  },
  
  setDiagramId: (id) => {
    set(state => {
      state.diagramId = id;
      // Don't increment version or record history for metadata changes
    });
  },
  
  setDiagramFormat: (format) => {
    set(state => {
      state.diagramFormat = format;
      // Don't increment version or record history for metadata changes
    });
  },
  
  clearDiagram: () => {
    set(state => {
      state.nodes.clear();
      state.arrows.clear();
      state.diagramName = 'Untitled';
      state.diagramDescription = '';
      state.diagramId = null;
      state.diagramFormat = null;
      // Arrays will be updated by afterChange
      afterChange(state);
    });
  },
  
  restoreDiagram: (nodes, arrows) => {
    set(state => {
      state.nodes = new Map(nodes);
      state.arrows = new Map(arrows);
      // Arrays will be updated by afterChange
      afterChange(state);
    });
  },
  
  restoreDiagramSilently: (nodes, arrows) => {
    set(state => {
      state.nodes = new Map(nodes);
      state.arrows = new Map(arrows);
      // No afterChange call - dataVersion not incremented
    });
  },
  
  triggerArraySync: () => {
    set(state => {
      state.dataVersion += 1;
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
    const nodeArray = Array.from(state.nodes.values());
    const hasStartNode = nodeArray.some(
      node => node.type === NodeType.START
    );
    if (!hasStartNode) {
      errors.push('Diagram must have at least one start node');
    }
    
    // Check for endpoint node
    const hasEndpoint = nodeArray.some(
      node => node.type === NodeType.ENDPOINT
    );
    if (!hasEndpoint) {
      errors.push('Diagram should have at least one endpoint node');
    }
    
    // Check for unconnected nodes
    const connectedNodes = new Set<string>();
    state.arrows.forEach(arrow => {
      const sourceNodeId = ConversionService.parseHandleId(arrow.source).node_id;
      const targetNodeId = ConversionService.parseHandleId(arrow.target).node_id;
      if (sourceNodeId) connectedNodes.add(sourceNodeId);
      if (targetNodeId) connectedNodes.add(targetNodeId);
    });
    
    const unconnectedNodes = nodeArray.filter(
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