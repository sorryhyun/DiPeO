import { create, StoreApi } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import { Draft } from "immer";
import { ArrowID, NodeID, PersonID, HandleID } from '@dipeo/models';
import { UnifiedStore, SetState, GetState } from "./types";
// import { logger } from "./middleware/debugMiddleware"; // TODO: implement if needed
// import { initializeArraySync } from "./middleware/arraySyncSubscriber"; // TODO: Implement if needed

import {
  createDiagramSlice,
  createComputedSlice,
  createExecutionSlice,
  createPersonSlice,
  createUISlice
} from "./slices";
import {
  createFullSnapshot,
  recordHistory
} from "./helpers/entityHelpers";
import { rebuildHandleIndex } from "./helpers/handleIndexHelper";

const devtoolsOptions = {
  serialize: {
    replacer: (key: string, value: unknown) => {
      if (value instanceof Map) {
        return {
          _type: 'Map',
          _value: Array.from(value.entries())
        };
      }
      return value;
    },
    reviver: (key: string, value: unknown) => {
      if (value && typeof value === 'object' && '_type' in value && value._type === 'Map' && '_value' in value) {
        return new Map(value._value as Array<[unknown, unknown]>);
      }
      return value;
    }
  }
};

const createStore = () => {
  const storeCreator = (set: SetState, get: GetState, api: StoreApi<UnifiedStore>): UnifiedStore => ({
        ...createDiagramSlice(set, get, api),
        ...createComputedSlice(set, get, api),
        ...createExecutionSlice(set, get, api),
        ...createPersonSlice(set, get, api),
        ...createUISlice(set, get, api),

        handles: new Map(),
        handleIndex: new Map(),
        history: {
          undoStack: [],
          redoStack: [],
          currentTransaction: null,
        },


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
            set((state) => {
              state.history.redoStack.push(createFullSnapshot(state));
              state.history.undoStack.pop();
            });

            state.restoreDiagramSilently(snapshot.nodes, snapshot.arrows);
            state.restorePersonsSilently(snapshot.persons);

            set((state) => {
              state.handles = new Map(snapshot.handles);
              state.handleIndex = rebuildHandleIndex(state.handles);
            });

            state.triggerArraySync();
          }
        },

        redo: () => {
          const state = get();
          if (state.history.redoStack.length === 0) return;

          const snapshot = state.history.redoStack[state.history.redoStack.length - 1];
          if (snapshot) {
            // Save current state to undo stack
            set((state) => {
              state.history.undoStack.push(createFullSnapshot(state));
              state.history.redoStack.pop();
            });

            // Use silent restore methods to avoid multiple dataVersion increments
            state.restoreDiagramSilently(snapshot.nodes, snapshot.arrows);
            state.restorePersonsSilently(snapshot.persons);

            // Restore unified store data
            set((state) => {
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
              // Use type assertion to avoid type instantiation depth errors
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              recordHistory(state as any);
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
          set((state) => {
            state.handles = new Map(snapshot.handles);
            state.handleIndex = rebuildHandleIndex(snapshot.handles);
          });

          // Trigger array sync once to update all arrays
          state.triggerArraySync();
        },

        // Handle cleanup method for node deletion
        cleanupNodeHandles: (nodeId: NodeID) => {
          set((state) => {
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
          set((state) => {
            state.handles = new Map();
            state.handleIndex = new Map();
          });
        },
  });

  // Apply middleware based on environment
  // Use explicit any type to avoid type instantiation depth errors with complex middleware chains
  // This is a known limitation with Zustand's middleware typing when combining immer, subscribeWithSelector, and devtools
  if (import.meta.env.DEV) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const withImmer = immer(storeCreator as any);
    const withSelector = subscribeWithSelector(withImmer);
    const withDevtools = devtools(withSelector, devtoolsOptions);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return create<UnifiedStore>()(withDevtools as any);
  }

  // Production build without logger
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const withImmer = immer(storeCreator as any);
  const withSelector = subscribeWithSelector(withImmer);
  const withDevtools = devtools(withSelector, devtoolsOptions);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return create<UnifiedStore>()(withDevtools as any);
};

export const useUnifiedStore = createStore();

// Initialize array synchronization
// initializeArraySync(useUnifiedStore); // TODO: Re-enable when middleware is implemented

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
