import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import {
  type ApiKeyID,
  type ArrowID,
  type DomainApiKey,
  type DomainArrow,
  type DomainNode,
  type DomainPerson,
  generateNodeId,
  generateArrowId,
  generatePersonId,
  type NodeID,
  type NodeKind,
  type PersonID,
  type Vec2,
  entityIdGenerators,
  apiKeyId
} from "@/types";
import { UnifiedStore, NodeState } from "./unifiedStore.types";
import { DiagramExporter } from "./diagramExporter";
import { loadAutoSavedDiagram, setupAutoSave } from "./persistedStore";
import { logger } from "@/utils/logger";

// Import helpers
import { 
  createFullSnapshot, 
  recordHistory, 
  updateMap 
} from "./helpers/entityHelpers";
import { 
  nodeCrud, 
  arrowCrud, 
  personCrud, 
  apiKeyCrud 
} from "./helpers/crudFactory";
import { 
  createNode, 
  importDiagram as importDiagramHelper 
} from "./helpers/importExportHelpers";

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
        dataVersion: 0,

        // Initial UI state
        selectedId: null,
        selectedType: null,
        activeView: 'diagram',
        activeCanvas: 'main',
        dashboardTab: 'properties',
        readOnly: false,
        executionReadOnly: false,
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

        // === Node Operations (using CRUD factory) ===
        addNode: (type, position, initialData) => {
          const node = createNode(type, position, initialData);
          set(state => {
            nodeCrud.add(state, node);
          });
          return node.id;
        },

        updateNode: (id, updates) => set(state => {
          nodeCrud.update(state, id, updates);
        }),

        updateNodeSilently: (id, updates) => set(state => {
          const nodes = updateMap(state.nodes, id, { ...state.nodes.get(id)!, ...updates });
          if (nodes) {
            state.nodes = nodes;
            state.dataVersion += 1;
          }
        }),

        deleteNode: (id) => set(state => {
          nodeCrud.delete(state, id);
        }),

        // === Arrow Operations ===
        addArrow: (source, target, data) => {
          const arrow: DomainArrow = {
            id: generateArrowId(),
            source,
            target,
            data: data || {},
          };
          set(state => {
            arrowCrud.add(state, arrow);
          });
          return arrow.id;
        },

        updateArrow: (id, updates) => set(state => {
          arrowCrud.update(state, id, updates);
        }),

        deleteArrow: (id) => set(state => {
          arrowCrud.delete(state, id);
        }),

        // === Person Operations ===
        addPerson: (label, service, model) => {
          const person: DomainPerson = {
            id: generatePersonId(),
            label,
            service,
            model,
            maxTokens: undefined,
            temperature: undefined,
            forgettingMode: 'no_forget',
          };
          set(state => {
            personCrud.add(state, person);
          });
          return person.id;
        },

        updatePerson: (id, updates) => set(state => {
          personCrud.update(state, id, updates);
        }),

        deletePerson: (id) => set(state => {
          personCrud.delete(state, id);
        }),

        // === API Key Operations ===
        addApiKey: (name, service) => {
          const id = apiKeyId(entityIdGenerators.apiKey());
          const apiKey: DomainApiKey = {
            id,
            label: name,
            service: service as DomainApiKey['service'],
          };
          set(state => {
            apiKeyCrud.add(state, apiKey);
          });
          return id;
        },

        updateApiKey: (id, updates) => set(state => {
          apiKeyCrud.update(state, id, updates);
        }),

        deleteApiKey: (id) => set(state => {
          apiKeyCrud.delete(state, id);
        }),

        // === Selection ===
        select: (id, type) => set(state => {
          state.selectedId = id as NodeID | ArrowID | PersonID;
          state.selectedType = type;
          state.dashboardTab = type === 'person' ? 'persons' : 'properties';
        }),

        clearSelection: () => set(state => {
          state.selectedId = null;
          state.selectedType = null;
        }),

        // === UI State ===
        setActiveCanvas: (canvas) => set(state => {
          state.activeCanvas = canvas;
        }),

        setReadOnly: (readOnly) => set(state => {
          state.readOnly = readOnly;
        }),

        setDashboardTab: (tab) => set(state => {
          state.dashboardTab = tab;
        }),

        openApiKeysModal: () => set(state => {
          state.showApiKeysModal = true;
        }),

        closeApiKeysModal: () => set(state => {
          state.showApiKeysModal = false;
        }),

        openExecutionModal: () => set(state => {
          state.showExecutionModal = true;
        }),

        closeExecutionModal: () => set(state => {
          state.showExecutionModal = false;
        }),

        // === Execution State ===
        startExecution: (executionId) => set(state => {
          state.execution = {
            id: executionId,
            isRunning: true,
            runningNodes: new Set(),
            nodeStates: new Map(),
            context: {},
          };
          state.activeView = 'execution';
          state.executionReadOnly = true;
        }),

        updateNodeExecution: (nodeId, nodeState) => set(state => {
          state.execution.nodeStates.set(nodeId, nodeState);
          
          if (nodeState.status === 'running') {
            state.execution.runningNodes.add(nodeId);
          } else {
            state.execution.runningNodes.delete(nodeId);
          }
        }),

        stopExecution: () => set(state => {
          state.execution.isRunning = false;
          state.execution.runningNodes = new Set();
          state.executionReadOnly = false;
        }),

        // === History Operations ===
        undo: () => set(state => {
          if (state.history.undoStack.length === 0) return;

          state.history.redoStack.push(createFullSnapshot(state));
          const snapshot = state.history.undoStack.pop();
          
          if (snapshot) {
            Object.assign(state, {
              nodes: new Map(snapshot.nodes),
              arrows: new Map(snapshot.arrows),
              persons: new Map(snapshot.persons),
              handles: new Map(snapshot.handles),
              apiKeys: new Map(snapshot.apiKeys),
            });
          }
        }),

        redo: () => set(state => {
          if (state.history.redoStack.length === 0) return;

          state.history.undoStack.push(createFullSnapshot(state));
          const snapshot = state.history.redoStack.pop();
          
          if (snapshot) {
            Object.assign(state, {
              nodes: new Map(snapshot.nodes),
              arrows: new Map(snapshot.arrows),
              persons: new Map(snapshot.persons),
              handles: new Map(snapshot.handles),
              apiKeys: new Map(snapshot.apiKeys),
            });
          }
        }),

        // === Transactions ===
        transaction: (fn) => {
          const transactionId = crypto.randomUUID();

          set(state => {
            state.history.currentTransaction = {
              id: transactionId,
              changes: [],
              timestamp: Date.now(),
            };
          });

          const result = fn();

          set(state => {
            if (state.history.currentTransaction) {
              recordHistory(state);
              state.history.currentTransaction = null;
            }
          });

          return result;
        },

        // === Utilities ===
        createSnapshot: () => createFullSnapshot(get()),

        restoreSnapshot: (snapshot) => set(state => {
          Object.assign(state, {
            nodes: new Map(snapshot.nodes),
            arrows: new Map(snapshot.arrows),
            persons: new Map(snapshot.persons),
            handles: new Map(snapshot.handles),
            apiKeys: new Map(snapshot.apiKeys),
            dataVersion: state.dataVersion + 1,
          });
        }),

        clearAll: () => set(state => {
          state.nodes = new Map();
          state.arrows = new Map();
          state.persons = new Map();
          state.handles = new Map();
          state.apiKeys = new Map();
          state.dataVersion = 0;
        }),

        // === Array selectors ===
        getNodes: () => Array.from(get().nodes.values()),
        getArrows: () => Array.from(get().arrows.values()),
        getPersons: () => Array.from(get().persons.values()),

        // === Export/Import ===
        exportDiagram: () => new DiagramExporter(get()).exportDiagram(),
        exportAsYAML: () => new DiagramExporter(get()).exportAsYAML(),
        importDiagram: (data) => set(state => importDiagramHelper(state, data)),
        validateExportData: (data) => new DiagramExporter(get()).validateExportData(data),
      }))
    )
  )
);

// Initialize store with auto-saved data
const initializeStore = () => {
  const autoSaved = loadAutoSavedDiagram();
  if (autoSaved) {
    try {
      logger.info('Restoring auto-saved diagram from', autoSaved.metadata?.exported);
      useUnifiedStore.getState().importDiagram(autoSaved);
    } catch (e) {
      logger.error('Failed to restore auto-saved diagram:', e);
    }
  }
  
  setupAutoSave(useUnifiedStore);
};

// Initialize on first import
if (typeof window !== 'undefined') {
  setTimeout(initializeStore, 0);
}

// === Selectors ===
export const useNodeById = (nodeId: NodeID | null) =>
  useUnifiedStore(state => nodeId ? state.nodes.get(nodeId) : null);

export const useArrowById = (arrowId: ArrowID | null) =>
  useUnifiedStore(state => arrowId ? state.arrows.get(arrowId) : null);

export const usePersonById = (personId: PersonID | null) =>
  useUnifiedStore(state => personId ? state.persons.get(personId) : null);

export const useNodes = () =>
  useUnifiedStore(state => Array.from(state.nodes.values()));

export const useArrows = () =>
  useUnifiedStore(state => Array.from(state.arrows.values()));

export const usePersons = () =>
  useUnifiedStore(state => Array.from(state.persons.values()));

export const useSelectedEntity = () =>
  useUnifiedStore(state => {
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
  useUnifiedStore(state => state.execution.isRunning);

export const useNodeExecutionState = (nodeId: NodeID) =>
  useUnifiedStore(state => state.execution.nodeStates.get(nodeId));