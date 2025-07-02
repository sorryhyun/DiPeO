import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import { ArrowID, NodeID, PersonID } from '@/core/types';
import { UnifiedStore } from "./unifiedStore.types";

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
  recordHistory 
} from "./helpers/entityHelpers";

// Custom serializer for Redux DevTools to handle Maps
const devtoolsOptions = {
  serialize: {
    // Custom replacer to handle Map serialization
    replacer: (key: string, value: unknown) => {
      if (value instanceof Map) {
        return {
          _type: 'Map',
          _value: Array.from(value.entries())
        };
      }
      return value;
    },
    // Custom reviver to restore Maps
    reviver: (key: string, value: unknown) => {
      if (value && typeof value === 'object' && '_type' in value && value._type === 'Map' && '_value' in value) {
        return new Map(value._value as Array<[unknown, unknown]>);
      }
      return value;
    }
  }
};

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
        
        // Initial history state
        history: {
          undoStack: [],
          redoStack: [],
          currentTransaction: null,
        },


        // === History Operations ===
        get canUndo() {
          return get().history.undoStack.length > 0;
        },
        
        get canRedo() {
          return get().history.redoStack.length > 0;
        },
        
        undo: () => set(state => {
          if (state.history.undoStack.length === 0) return;

          state.history.redoStack.push(createFullSnapshot(state));
          const snapshot = state.history.undoStack.pop();
          
          if (snapshot) {
            Object.assign(state, {
              nodes: new Map(snapshot.nodes),
              arrows: new Map(snapshot.arrows),
              persons: new Map(snapshot.persons),
              handles: new Map(snapshot.handles)
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
              handles: new Map(snapshot.handles)
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
          state.nodesArray = [];
          state.arrowsArray = [];
          state.personsArray = [];
          state.dataVersion = 0;
        }),

      }))
    ),
    devtoolsOptions
  )
);

// Store initialization is now handled by the backend
// Auto-save and diagram persistence are managed through GraphQL

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