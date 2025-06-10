import { create } from "zustand";
import {devtools, subscribeWithSelector} from "zustand/middleware";
import {immer} from "zustand/middleware/immer";
import {
    type ApiKeyID,
    type ArrowID, type DomainApiKey,
    type DomainArrow,
    type DomainHandle, type DomainNode,
    type DomainPerson, entityIdGenerators,
    generateArrowId,
    generateNodeId,
    generatePersonId, type NodeID, type NodeKind, type PersonID, type Vec2,
    connectsToNode
} from "@/types";
import {generateNodeHandlesFromRegistry} from "@/utils";
import {UnifiedStore, Snapshot, ExportFormat} from "./unifiedStore.types";
import {DiagramExporter} from "./diagramExporter";

// Helper function to create a snapshot
function createSnapshot(state: Partial<UnifiedStore>): Snapshot {
  return {
    nodes: new Map(state.nodes || new Map()),
    arrows: new Map(state.arrows || new Map()),
    persons: new Map(state.persons || new Map()),
    handles: new Map(state.handles || new Map()),
    apiKeys: new Map(state.apiKeys || new Map()),
    timestamp: Date.now(),
  };
}

// Helper function to create a node
function createNode(type: NodeKind, position: Vec2, initialData?: Record<string, unknown>): DomainNode {
  const id = generateNodeId();
  const baseNode: DomainNode = {
    id,
    type,
    position: {
      x: position?.x ?? 0,
      y: position?.y ?? 0
    },
    data: {
      label: initialData?.label || `${type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')} ${id.split('-').pop()}`,
      ...(initialData || {})
    },
  };

  // Type-specific initialization
  switch (type) {
    case 'start':
      return { ...baseNode, data: { ...baseNode.data, data: initialData?.data || '' } };
    case 'condition':
      return { ...baseNode, data: { ...baseNode.data, condition: initialData?.condition || '' } };
    case 'job':
      return { ...baseNode, data: { ...baseNode.data, code: initialData?.code || '', language: 'python' } };
    case 'person_job':
      return {
        ...baseNode,
        data: {
          ...baseNode.data,
          personId: initialData?.personId || null,
          firstOnlyPrompt: initialData?.firstOnlyPrompt || '',
          defaultPrompt: initialData?.defaultPrompt || '',
          maxIterations: initialData?.maxIterations || 1,
        },
      };
    case 'db':
      return {
        ...baseNode,
        data: {
          ...baseNode.data,
          operation: initialData?.operation || 'create',
          key: initialData?.key || '',
          value: initialData?.value || '',
        },
      };
    case 'user_response':
      return {
        ...baseNode,
        data: {
          ...baseNode.data,
          prompt: initialData?.prompt || '',
          timeout: initialData?.timeout || 30,
        },
      };
    case 'notion':
      return {
        ...baseNode,
        data: {
          ...baseNode.data,
          operation: initialData?.operation || 'read',
          pageId: initialData?.pageId || '',
        },
      };
    case 'endpoint':
      return {
        ...baseNode,
        data: {
          ...baseNode.data,
          operation: initialData?.operation || 'return',
          data: initialData?.data || '',
        },
      };
    case 'person_batch_job':
      return {
        ...baseNode,
        data: {
          ...baseNode.data,
          personId: initialData?.personId || null,
          batchSize: initialData?.batchSize || 5,
          prompt: initialData?.prompt || '',
        },
      };
    default:
      return baseNode;
  }
}

export const useUnifiedStore = create<UnifiedStore>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // Initialize all data structures
        nodes: new Map(),
        arrows: new Map(),
        persons: new Map(),
        handles: new Map(),
        apiKeys: new Map(),

        // Initial UI state
        selectedId: null,
        selectedType: null,
        activeView: 'diagram',
        activeCanvas: 'main',
        dashboardTab: 'properties',
        readOnly: false,
        showApiKeysModal: false,
        showExecutionModal: false,

        // Initial execution state
        execution: {
          id: null,
          isRunning: false,
          runningNodes: new Set(),
          nodeStates: new Map(),
          context: {},
        },

        // Initial history state
        history: {
          undoStack: [],
          redoStack: [],
          currentTransaction: null,
        },

        // Actions with automatic history tracking
        addNode: (type, position, initialData) => {
          const nodeId = generateNodeId();

          set((state) => {
            const node = createNode(type, position, initialData);
            node.id = nodeId;

            // Add node
            state.nodes.set(nodeId, node);

            // Auto-generate handles
            const handles = generateNodeHandlesFromRegistry(nodeId, type);
            handles.forEach((handle: DomainHandle) => {
              state.handles.set(handle.id, handle);
            });

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          });

          return nodeId;
        },

        updateNode: (id, updates) =>
          set((state) => {
            const node = state.nodes.get(id);
            if (!node) return;

            // Deep merge data if provided in updates
            if (updates.data && node.data) {
              updates = {
                ...updates,
                data: {
                  ...node.data,
                  ...updates.data
                }
              };
            }

            // Update node
            Object.assign(node, updates);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        deleteNode: (id) =>
          set((state) => {
            const node = state.nodes.get(id);
            if (!node) return;

            // Delete node
            state.nodes.delete(id);

            // Delete associated handles
            Array.from(state.handles.values()).forEach((handle) => {
              if (handle.nodeId === id) {
                state.handles.delete(handle.id);
              }
            });

            // Delete connected arrows
            Array.from(state.arrows.values()).forEach((arrow) => {
              if (connectsToNode(arrow, id)) {
                state.arrows.delete(arrow.id);
              }
            });

            // Clear selection if deleted
            if (state.selectedId === id) {
              state.selectedId = null;
              state.selectedType = null;
            }

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        // Arrow operations
        addArrow: (source, target, data) => {
          const arrowId = generateArrowId();

          set((state) => {
            const arrow: DomainArrow = {
              id: arrowId,
              source,
              target,
              data: data || {},
            };

            state.arrows.set(arrowId, arrow);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          });

          return arrowId;
        },

        updateArrow: (id, updates) =>
          set((state) => {
            const arrow = state.arrows.get(id);
            if (!arrow) return;

            Object.assign(arrow, updates);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        deleteArrow: (id) =>
          set((state) => {
            state.arrows.delete(id);

            // Clear selection if deleted
            if (state.selectedId === id) {
              state.selectedId = null;
              state.selectedType = null;
            }

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        // Person operations
        addPerson: (name, service, model) => {
          const personId = generatePersonId();

          set((state) => {
            const person: DomainPerson = {
              id: personId,
              name,
              service,
              model,
              maxTokens: undefined,
              temperature: undefined,
              forgettingMode: 'no_forget',
            };

            state.persons.set(personId, person);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          });

          return personId;
        },

        updatePerson: (id, updates) =>
          set((state) => {
            const person = state.persons.get(id);
            if (!person) return;

            Object.assign(person, updates);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        deletePerson: (id) =>
          set((state) => {
            state.persons.delete(id);

            // Clear selection if deleted
            if (state.selectedId === id) {
              state.selectedId = null;
              state.selectedType = null;
            }

            // Update nodes that reference this person
            state.nodes.forEach((node) => {
              if (
                (node.type === 'person_job' || node.type === 'person_batch_job') &&
                node.data.personId === id
              ) {
                node.data.personId = null;
              }
            });

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        // Selection with proper cleanup
        select: (id, type) =>
          set((state) => {
            state.selectedId = id as NodeID | ArrowID | PersonID;
            state.selectedType = type;

            // Automatically switch to appropriate tab
            state.dashboardTab = type === 'person' ? 'persons' : 'properties';
          }),

        clearSelection: () =>
          set((state) => {
            state.selectedId = null;
            state.selectedType = null;
          }),

        // UI State management
        setActiveCanvas: (canvas) =>
          set((state) => {
            state.activeCanvas = canvas;
          }),

        setReadOnly: (readOnly) =>
          set((state) => {
            state.readOnly = readOnly;
          }),

        setDashboardTab: (tab) =>
          set((state) => {
            state.dashboardTab = tab;
          }),

        openApiKeysModal: () =>
          set((state) => {
            state.showApiKeysModal = true;
          }),

        closeApiKeysModal: () =>
          set((state) => {
            state.showApiKeysModal = false;
          }),

        openExecutionModal: () =>
          set((state) => {
            state.showExecutionModal = true;
          }),

        closeExecutionModal: () =>
          set((state) => {
            state.showExecutionModal = false;
          }),

        // API Key operations
        addApiKey: (name, service) => {
          const rawId = entityIdGenerators.apiKey();
          const id = rawId as ApiKeyID;

          set((state) => {
            const apiKey: DomainApiKey = {
              id,
              name,
              service: service as DomainApiKey['service'],
            };

            state.apiKeys.set(id, apiKey);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          });

          return id;
        },

        updateApiKey: (id, updates) =>
          set((state) => {
            const apiKey = state.apiKeys.get(id);
            if (!apiKey) return;

            // Update API key
            Object.assign(apiKey, updates);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        deleteApiKey: (id) =>
          set((state) => {
            state.apiKeys.delete(id);

            // Record history if not in transaction
            if (!state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
            }
          }),

        // Execution state management
        startExecution: (executionId) =>
          set((state) => {
            state.execution.id = executionId;
            state.execution.isRunning = true;
            state.execution.runningNodes.clear();
            state.execution.nodeStates.clear();
            state.execution.context = {};
            state.activeView = 'execution';
          }),

        updateNodeExecution: (nodeId, nodeState) =>
          set((state) => {
            state.execution.nodeStates.set(nodeId, nodeState);

            if (nodeState.status === 'running') {
              state.execution.runningNodes.add(nodeId);
            } else {
              state.execution.runningNodes.delete(nodeId);
            }
          }),

        stopExecution: () =>
          set((state) => {
            state.execution.isRunning = false;
            state.execution.runningNodes.clear();
          }),

        // History operations
        undo: () =>
          set((state) => {
            if (state.history.undoStack.length === 0) return;

            // Save current state to redo stack
            state.history.redoStack.push(createSnapshot(state));

            // Pop from undo stack and restore
            const snapshot = state.history.undoStack.pop();
            if (snapshot) {
              state.nodes = new Map(snapshot.nodes);
              state.arrows = new Map(snapshot.arrows);
              state.persons = new Map(snapshot.persons);
              state.handles = new Map(snapshot.handles);
              state.apiKeys = new Map(snapshot.apiKeys);
            }
          }),

        redo: () =>
          set((state) => {
            if (state.history.redoStack.length === 0) return;

            // Save current state to undo stack
            state.history.undoStack.push(createSnapshot(state));

            // Pop from redo stack and restore
            const snapshot = state.history.redoStack.pop();
            if (snapshot) {
              state.nodes = new Map(snapshot.nodes);
              state.arrows = new Map(snapshot.arrows);
              state.persons = new Map(snapshot.persons);
              state.handles = new Map(snapshot.handles);
              state.apiKeys = new Map(snapshot.apiKeys);
            }
          }),

        // Batch operations with transactions
        transaction: (fn) => {
          const transactionId = crypto.randomUUID();

          set((state) => {
            state.history.currentTransaction = {
              id: transactionId,
              changes: [],
              timestamp: Date.now(),
            };
          });

          const result = fn();

          set((state) => {
            if (state.history.currentTransaction) {
              state.history.undoStack.push(createSnapshot(state));
              state.history.redoStack = [];
              state.history.currentTransaction = null;
            }
          });

          return result;
        },

        // Utilities
        createSnapshot: () => createSnapshot(get()),

        restoreSnapshot: (snapshot) =>
          set((state) => {
            state.nodes = new Map(snapshot.nodes);
            state.arrows = new Map(snapshot.arrows);
            state.persons = new Map(snapshot.persons);
            state.handles = new Map(snapshot.handles);
            state.apiKeys = new Map(snapshot.apiKeys);
          }),

        // Export/Import operations
        exportDiagram: () => {
          const exporter = new DiagramExporter(get());
          return exporter.exportDiagram();
        },

        exportAsJSON: () => {
          const exporter = new DiagramExporter(get());
          return exporter.exportAsJSON();
        },

        importDiagram: (data: ExportFormat | string) => {
          const exporter = new DiagramExporter(get());
          exporter.importDiagram(data);
        },

        validateExportData: (data: unknown) => {
          const exporter = new DiagramExporter(get());
          return exporter.validateExportData(data);
        },
      }))
    )
  )
);

// Selectors for common operations
export const useNodeById = (nodeId: NodeID | null) =>
  useUnifiedStore((state) => (nodeId ? state.nodes.get(nodeId) : null));

export const useArrowById = (arrowId: ArrowID | null) =>
  useUnifiedStore((state) => (arrowId ? state.arrows.get(arrowId) : null));

export const usePersonById = (personId: PersonID | null) =>
  useUnifiedStore((state) => (personId ? state.persons.get(personId) : null));

export const useSelectedEntity = () =>
  useUnifiedStore((state) => {
    if (!state.selectedId || !state.selectedType) return null;

    switch (state.selectedType) {
      case 'node':
        return state.nodes.get(state.selectedId as NodeID);
      case 'arrow':
        return state.arrows.get(state.selectedId as ArrowID);
      case 'person':
        return state.persons.get(state.selectedId as PersonID);
      default:
        return null;
    }
  });

export const useIsExecuting = () =>
  useUnifiedStore((state) => state.execution.isRunning);

export const useNodeExecutionState = (nodeId: NodeID) =>
  useUnifiedStore((state) => state.execution.nodeStates.get(nodeId));