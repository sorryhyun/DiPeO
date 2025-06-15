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

// Import slices
import {
  createDiagramSlice,
  createComputedSlice,
  createExecutionSlice,
  createPersonSlice,
  createUISlice
} from "./slices";

// Import helpers
import { 
  createFullSnapshot, 
  recordHistory, 
  updateMap 
} from "./helpers/entityHelpers";
import { 
  apiKeyCrud 
} from "./helpers/crudFactory";

export const useUnifiedStore = create<UnifiedStore>()(
  devtools(
    subscribeWithSelector(
      immer((set, get, api) => ({
        // Compose all slices
        ...createDiagramSlice(set, get, api),
        ...createComputedSlice(set, get, api),
        ...createExecutionSlice(set, get, api),
        ...createPersonSlice(set, get, api),
        ...createUISlice(set, get, api),
        
        // Additional data not in slices
        handles: new Map(),
        apiKeys: new Map(),
        
        // Initial history state
        history: {
          undoStack: [],
          redoStack: [],
          currentTransaction: null,
        },

        // === API Key Operations ===
        addApiKey: (name, service) => {
          const id = apiKeyId(entityIdGenerators.apiKey());
          const apiKey: DomainApiKey = {
            id,
            label: name,
            service: service as DomainApiKey['service'],
            maskedKey: '••••••••'
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
            
            // Update arrays after restoring maps
            state.nodesArray = Array.from(state.nodes.values());
            state.arrowsArray = Array.from(state.arrows.values());
            state.personsArray = Array.from(state.persons.values());
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
            
            // Update arrays after restoring maps
            state.nodesArray = Array.from(state.nodes.values());
            state.arrowsArray = Array.from(state.arrows.values());
            state.personsArray = Array.from(state.persons.values());
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
          
          // Update arrays after restoring maps
          state.nodesArray = Array.from(state.nodes.values());
          state.arrowsArray = Array.from(state.arrows.values());
          state.personsArray = Array.from(state.persons.values());
        }),

        clearAll: () => set(state => {
          state.nodes = new Map();
          state.arrows = new Map();
          state.persons = new Map();
          state.handles = new Map();
          state.apiKeys = new Map();
          state.nodesArray = [];
          state.arrowsArray = [];
          state.personsArray = [];
          state.dataVersion = 0;
        }),

        // === Legacy Array selectors (for backward compatibility) ===
        getNodes: () => get().nodesArray,
        getArrows: () => get().arrowsArray,
        getPersons: () => get().personsArray,

        // === Export/Import ===
        exportDiagram: () => new DiagramExporter(get()).exportDiagram(),
        exportAsYAML: () => new DiagramExporter(get()).exportAsYAML(),
        importDiagram: (data, format) => {
          const exporter = new DiagramExporter(get());
          exporter.importDiagram(data, format);
        },
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
  useUnifiedStore(state => state.nodesArray);

export const useArrows = () =>
  useUnifiedStore(state => state.arrowsArray);

export const usePersons = () =>
  useUnifiedStore(state => state.personsArray);

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