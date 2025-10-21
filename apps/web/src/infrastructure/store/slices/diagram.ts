import { ArrowID, DomainArrow, DomainNode, NodeID, HandleID } from '@/infrastructure/types';
import { generateArrowId } from '@/infrastructure/types/utilities';
import {
  Converters,
  NodeFactory,
  NodeService,
  ValidationService,
  DiagramOperations
} from '@/infrastructure/services';
import { NodeType, Vec2, DiagramFormat, DomainDiagram, DiagramMetadata } from '@dipeo/models';
import type { UnifiedStore, SetState, GetState, StoreApiType } from '../types';

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

  // Import/Export operations
  importDiagram: (jsonString: string) => Promise<{ success: boolean; error?: string }>;
  exportDiagram: (pretty?: boolean) => string;

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
  // Update computed arrays when Maps change
  state.nodesArray = Array.from(state.nodes.values());
  state.arrowsArray = Array.from(state.arrows.values());
  state.handlesArray = Array.from(state.handles.values());
  // recordHistory(state);
};

export const createDiagramSlice = (
  set: SetState,
  get: GetState,
  _api: StoreApiType
): DiagramSlice => ({
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
    // Use NodeFactory for type-safe node creation with validation
    const result = NodeFactory.createNodeWithValidation(type, position, initialData);

    if (!result.success) {
      console.error('Failed to create node:', result.error);
      // Fall back to creating without validation for backward compatibility
      const node = NodeFactory.createNode(type, position, initialData);
      set(state => {
        state.nodes.set(Converters.toNodeId(node.id), node);
        afterChange(state);
      });
      return Converters.toNodeId(node.id);
    }

    const node = result.data;
    set(state => {
      state.nodes.set(Converters.toNodeId(node.id), node);
      afterChange(state);
    });
    return Converters.toNodeId(node.id);
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
        // Silent update - no version increment, history, or array sync
        // Used for intermediate updates during operations
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
            const sourceNodeId = Converters.parseHandleId(arrow.source).node_id;
            const targetNodeId = Converters.parseHandleId(arrow.target).node_id;
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
      (arrow as { content_type?: string }).content_type = content_type;
    }
    if (label !== undefined && label !== null) {
      arrow.label = label;
    }

    set(state => {
      // Validate source and target nodes exist

      let sourceNodeId: NodeID;
      let targetNodeId: NodeID;

      try {
        const sourceParsed = Converters.parseHandleId(Converters.toHandleId(source));
        const targetParsed = Converters.parseHandleId(Converters.toHandleId(target));
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

      state.arrows.set(Converters.toArrowId(arrow.id), arrow);
      afterChange(state);
    });

    return Converters.toArrowId(arrow.id);
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
              const sourceNodeId = Converters.parseHandleId(arrow.source).node_id;
              const targetNodeId = Converters.parseHandleId(arrow.target).node_id;
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
      afterChange(state as UnifiedStore);
    });
  },

  restoreDiagram: (nodes, arrows) => {
    set(state => {
      state.nodes = new Map(nodes);
      state.arrows = new Map(arrows);
      afterChange(state as UnifiedStore);
    });
  },

  restoreDiagramSilently: (nodes, arrows) => {
    set(state => {
      state.nodes = new Map(nodes);
      state.arrows = new Map(arrows);
      // Update arrays but don't increment version or record history
      state.nodesArray = Array.from(state.nodes.values());
      state.arrowsArray = Array.from(state.arrows.values());
      state.handlesArray = Array.from(state.handles.values());
    });
  },

  triggerArraySync: () => {
    set(state => {
      // Update all arrays from their Maps
      state.nodesArray = Array.from(state.nodes.values());
      state.arrowsArray = Array.from(state.arrows.values());
      state.personsArray = Array.from(state.persons.values());
      state.handlesArray = Array.from(state.handles.values());
      // Keep dataVersion for backward compatibility but it's not critical
      state.dataVersion += 1;
    });
  },

  validateDiagram: () => {
    const state = get();

    // Create a DomainDiagram from the current state
    const diagram: DomainDiagram = {
      nodes: Array.from(state.nodes.values()),
      handles: Array.from(state.handles.values()),
      arrows: Array.from(state.arrows.values()),
      persons: Array.from(state.persons.values())
    };

    // Use ValidationService for comprehensive validation
    const validationResult = ValidationService.validateDiagram(diagram);

    // Convert validation result to expected format
    const errors: string[] = [];

    // Add node errors
    if (validationResult.nodeErrors) {
      validationResult.nodeErrors.forEach((fieldErrors, nodeId) => {
        const node = state.nodes.get(nodeId as NodeID);
        const nodeLabel = node?.data?.label || nodeId;
        if (Array.isArray(fieldErrors)) {
          fieldErrors.forEach((error) => {
            errors.push(`Node ${nodeLabel}: ${error.field} - ${error.message}`);
          });
        }
      });
    }

    // Add connection errors
    if (validationResult.connectionErrors) {
      validationResult.connectionErrors.forEach((error) => {
        errors.push(error.message);
      });
    }

    // Add general errors
    if (validationResult.generalErrors) {
      validationResult.generalErrors.forEach((error) => {
        errors.push(error.message);
      });
    }

    // Add additional person assignment check
    state.nodes.forEach(node => {
      if (node.type === NodeType.PERSON_JOB && !node.data?.person) {
        errors.push(`Node ${node.data?.label || node.id} requires a person to be assigned`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Import/Export operations
  importDiagram: async (jsonString) => {
    try {
      const result = await DiagramOperations.importDiagram(jsonString);

      if (!result.success) {
        return { success: false, error: result.errors?.join(', ') || 'Import failed' };
      }

      if (!result.diagram) {
        return { success: false, error: 'No diagram data found' };
      }

      const diagram = result.diagram;
      const metadata = diagram.metadata as DiagramMetadata | null | undefined;

      // Clear current diagram
      get().clearDiagram();

      // Set metadata with proper type guards
      set(state => {
        if (metadata?.name && typeof metadata.name === 'string') {
          state.diagramName = metadata.name;
        }
        if (metadata?.description && typeof metadata.description === 'string') {
          state.diagramDescription = metadata.description;
        }
        if (metadata?.id && typeof metadata.id === 'string') {
          state.diagramId = metadata.id;
        }
        if (metadata?.format && typeof metadata.format === 'string') {
          state.diagramFormat = metadata.format as DiagramFormat;
        }
      });

      // Restore nodes and arrows
      const { nodes, arrows } = Converters.diagramArraysToMaps(diagram);
      get().restoreDiagram(nodes, arrows);

      return { success: true };
    } catch (error) {
      console.error('Failed to import diagram:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  exportDiagram: (pretty = false) => {
    const state = get();

    // Create DomainDiagram from current state
    const diagram: DomainDiagram = {
      nodes: Array.from(state.nodes.values()),
      handles: Array.from(state.handles.values()),
      arrows: Array.from(state.arrows.values()),
      persons: Array.from(state.persons.values())
    };

    // Use DiagramOperations for export
    return DiagramOperations.exportDiagram(diagram, pretty);
  }
});
