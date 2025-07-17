import { create, StateCreator } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import { ArrowID, NodeID, PersonID, HandleID } from '@/core/types';
import { UnifiedStore } from "./unifiedStore.types";
import { logger } from "./middleware/debugMiddleware";
import { initializeArraySync } from "./middleware/arraySyncSubscriber";

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
import { rebuildHandleIndex } from "./helpers/handleIndexHelper";

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

const createStore = () => {
  const storeCreator: StateCreator<
    UnifiedStore,
    [['zustand/immer', never]],
    [],
    UnifiedStore
  > = (set, get, api) => ({
        // Compose all slices
        ...createDiagramSlice(set, get, api),
        ...createComputedSlice(set, get, api),
        ...createExecutionSlice(set, get, api),
        ...createPersonSlice(set, get, api),
        ...createUISlice(set, get, api),
        
        // Additional data not in slices
        handles: new Map(),
        handleIndex: new Map(),
        
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
        
        undo: () => {
          const state = get();
          if (state.history.undoStack.length === 0) return;

          const snapshot = state.history.undoStack[state.history.undoStack.length - 1];
          if (snapshot) {
            // Save current state to redo stack
            set(state => {
              state.history.redoStack.push(createFullSnapshot(state));
              state.history.undoStack.pop();
            });
            
            // Use silent restore methods to avoid multiple dataVersion increments
            state.restoreDiagramSilently(snapshot.nodes, snapshot.arrows);
            state.restorePersonsSilently(snapshot.persons);
            
            // Restore unified store data
            set(state => {
              state.handles = new Map(snapshot.handles);
              state.handleIndex = rebuildHandleIndex(state.handles);
            });
            
            // Trigger array sync once through the diagram slice
            state.triggerArraySync();
          }
        },

        redo: () => {
          const state = get();
          if (state.history.redoStack.length === 0) return;

          const snapshot = state.history.redoStack[state.history.redoStack.length - 1];
          if (snapshot) {
            // Save current state to undo stack
            set(state => {
              state.history.undoStack.push(createFullSnapshot(state));
              state.history.redoStack.pop();
            });
            
            // Use silent restore methods to avoid multiple dataVersion increments
            state.restoreDiagramSilently(snapshot.nodes, snapshot.arrows);
            state.restorePersonsSilently(snapshot.persons);
            
            // Restore unified store data
            set(state => {
              state.handles = new Map(snapshot.handles);
              state.handleIndex = rebuildHandleIndex(state.handles);
            });
            
            // Trigger array sync once through the diagram slice
            state.triggerArraySync();
          }
        },

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

        restoreSnapshot: (snapshot) => {
          const state = get();
          
          // Use silent restore methods to avoid multiple dataVersion increments
          state.restoreDiagramSilently(snapshot.nodes, snapshot.arrows);
          state.restorePersonsSilently(snapshot.persons);
          
          // Update UnifiedStore-specific data
          set(state => {
            state.handles = new Map(snapshot.handles);
            state.handleIndex = rebuildHandleIndex(snapshot.handles);
          });
          
          // Trigger array sync once through the diagram slice
          state.triggerArraySync();
        },

        // Handle cleanup method for node deletion
        cleanupNodeHandles: (nodeId: NodeID) => {
          set(state => {
            const handleIdsToDelete: HandleID[] = [];
            state.handles.forEach((handle, handleId) => {
              if (handle.node_id === nodeId) {
                handleIdsToDelete.push(handleId);
              }
            });
            
            handleIdsToDelete.forEach(handleId => {
              state.handles.delete(handleId);
            });
            
            state.handleIndex.delete(nodeId);
          });
        },
        
        clearAll: () => {
          const state = get();
          // Use slice methods to clear data properly
          state.clearDiagram();
          state.clearPersons();
          state.stopExecution();
          state.clearUIState();
          
          // Clear unified store specific data
          set(state => {
            state.handles = new Map();
            state.handleIndex = new Map();
          });
        },
  });

  // Apply middleware based on environment
  if (import.meta.env.DEV) {
    return create<UnifiedStore>()(
      logger(
        devtools(
          subscribeWithSelector(
            immer(storeCreator)
          ),
          devtoolsOptions
        ),
        'UnifiedStore'
      )
    );
  }

  // Production build without logger
  return create<UnifiedStore>()(
    devtools(
      subscribeWithSelector(
        immer(storeCreator)
      ),
      devtoolsOptions
    )
  );
};

export const useUnifiedStore = createStore();

// Initialize array synchronization
initializeArraySync(useUnifiedStore);

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

export const useDiagramFormat = () =>
  useUnifiedStore(state => state.diagramFormat);