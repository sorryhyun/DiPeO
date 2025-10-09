import { create, StateCreator, StoreApi } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { Draft } from 'immer';
import {
  UnifiedStore,
  StoreSnapshot,
  Transaction,
  SetState,
  GetState,
} from './types';
import { sideEffectsMiddleware, registerDefaultSideEffects } from './middleware/sideEffects';
import { DomainNode, DomainArrow, DomainPerson, DomainHandle, NodeID, ArrowID, PersonID } from '@dipeo/models';

// Import slices
import { createDiagramSlice } from './slices/diagram';
import { createExecutionSlice } from './slices/execution';
import { createPersonSlice } from './slices/person';
import { createUISlice } from './slices/ui';
import { createComputedSlice } from './slices/computedSlice';

// Re-export types and utilities
export * from './types';
export {
  selectNodes,
  selectArrows,
  selectPersons,
  selectHandles,
  selectNodeById,
  selectArrowById,
  selectPersonById,
  selectNodesArray,
  selectArrowsArray,
  selectPersonsArray,
  selectNodesByType,
  selectConnectedArrows,
  selectIncomingArrows,
  selectOutgoingArrows,
  selectSelectedEntity,
  selectIsSelected,
  selectSelectionType,
  selectIsExecuting,
  selectExecutionStatus,
  selectNodeExecutionState,
  selectExecutionProgress,
  selectExecutionError,
  selectDiagramName,
  selectDiagramDescription,
  selectDiagramId,
  selectDiagramFormat,
  selectDataVersion,
  selectCanUndo,
  selectCanRedo,
  selectHistoryLength,
  selectDiagramStatistics,
  selectValidationState,
  selectExecutionSummary,
  selectGraphStructure,
} from './selectors';
export * from './actions/patterns';
export * from './middleware/sideEffects';

// ===== Store Configuration =====

export interface StoreConfig {
  enableDevtools: boolean;
  enableLogging: boolean;
  enablePersistence: boolean;
  persistenceKey?: string;
  middleware?: StoreMiddleware[];
}

export interface StoreMiddleware {
  name: string;
  before?: (context: MiddlewareContext) => void;
  after?: (context: MiddlewareContext) => void;
}

export interface MiddlewareContext {
  action: string;
  payload: unknown;
  timestamp: number;
  userId?: string;
}

const defaultConfig: StoreConfig = {
  enableDevtools: process.env.NODE_ENV === 'development',
  enableLogging: process.env.NODE_ENV === 'development',
  enablePersistence: false,
  persistenceKey: 'dipeo-store',
  middleware: [],
};

// ===== Helper Functions =====

function createSnapshot(state: UnifiedStore): StoreSnapshot {
  return {
    nodes: new Map(state.nodes),
    arrows: new Map(state.arrows),
    persons: new Map(state.persons),
    handles: new Map(state.handles),
    timestamp: Date.now(),
  };
}

function restoreSnapshot(state: UnifiedStore, snapshot: StoreSnapshot): void {
  // Restore nodes and arrows
  state.nodes = new Map(snapshot.nodes);
  state.arrows = new Map(snapshot.arrows);

  // Restore persons
  state.persons = new Map(snapshot.persons);

  // Restore handles
  state.handles = new Map(snapshot.handles);

  // Rebuild handle index
  state.handleIndex.clear();
  snapshot.handles.forEach((handle, handleId) => {
    const nodeHandles = state.handleIndex.get(handle.node_id) || [];
    nodeHandles.push(handle);
    state.handleIndex.set(handle.node_id, nodeHandles);
  });

  // Trigger updates
  state.dataVersion++;
}

// ===== Main Store Creator =====

function createUnifiedStore(config: Partial<StoreConfig> = {}) {
  const finalConfig = { ...defaultConfig, ...config };

  const storeCreator = (set: SetState, get: GetState, api: StoreApi<UnifiedStore>): UnifiedStore => {
    // Create slice instances
    const diagramSlice = createDiagramSlice(set, get, api);
    const executionSlice = createExecutionSlice(set, get, api);
    const personSlice = createPersonSlice(set, get, api);
    const uiSlice = createUISlice(set, get, api);
    const computedSlice = createComputedSlice(set, get, api);

    return {
      // ===== Spread all slice properties (flattened) =====
      ...diagramSlice,
      ...executionSlice,
      ...personSlice,
      ...uiSlice,
      ...computedSlice,

      // ===== Additional Core Data =====
      handles: new Map(),
      handleIndex: new Map(),

      // ===== History =====
      history: {
        undoStack: [],
        redoStack: [],
        currentTransaction: null,
      },

      // ===== Computed Values =====
      get nodesArray(): DomainNode[] {
        return Array.from(get().nodes.values());
      },

      get arrowsArray(): DomainArrow[] {
        return Array.from(get().arrows.values());
      },

      get personsArray(): DomainPerson[] {
        return Array.from(get().persons.values());
      },

      get canUndo() {
        return get().history.undoStack.length > 0;
      },

      get canRedo() {
        return get().history.redoStack.length > 0;
      },

      // ===== History Actions =====
      undo: () => {
        const state = get();
        if (state.history.undoStack.length === 0) return;

        const previousSnapshot = state.history.undoStack[state.history.undoStack.length - 1];
        const currentSnapshot = createSnapshot(state);

        if (previousSnapshot) {
          set((draft) => {
            draft.history.undoStack.pop();
            draft.history.redoStack.push(currentSnapshot);
            // Use type assertion to avoid type instantiation depth errors
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            restoreSnapshot(draft as any, previousSnapshot);
          });
        }
      },

      redo: () => {
        const state = get();
        if (state.history.redoStack.length === 0) return;

        const nextSnapshot = state.history.redoStack[state.history.redoStack.length - 1];
        const currentSnapshot = createSnapshot(state);

        if (nextSnapshot) {
          set((draft) => {
            draft.history.redoStack.pop();
            draft.history.undoStack.push(currentSnapshot);
            // Use type assertion to avoid type instantiation depth errors
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            restoreSnapshot(draft as any, nextSnapshot);
          });
        }
      },

      // ===== Additional Actions =====
      createSnapshot: () => createSnapshot(get()),

      restoreSnapshot: (snapshot: StoreSnapshot) => {
        set((draft) => {
          // Use type assertion to avoid type instantiation depth errors
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          restoreSnapshot(draft as any, snapshot);
        });
      },

      cleanupNodeHandles: (nodeId: NodeID) => {
        set((draft) => {
          const handleIds = draft.handleIndex.get(nodeId) || [];
          handleIds.forEach((handle: DomainHandle) => {
            draft.handles.delete(handle.id);
          });
          draft.handleIndex.delete(nodeId);
        });
      },

      transaction<T>(fn: () => T): T {
        const transactionId = crypto.randomUUID();
        const beforeSnapshot = createSnapshot(get());

        set((draft) => {
          draft.history.currentTransaction = {
            id: transactionId,
            changes: [],
            timestamp: Date.now(),
          };
        });

        try {
          const result = fn();

          set((draft) => {
            if (draft.history.currentTransaction?.id === transactionId) {
              draft.history.undoStack.push(beforeSnapshot);
              draft.history.currentTransaction = null;
              // Clear redo stack on new action
              draft.history.redoStack = [];
            }
          });

          return result;
        } catch (error) {
          // Rollback on error
          set((draft) => {
            // Use type assertion to avoid type instantiation depth errors
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            restoreSnapshot(draft as any, beforeSnapshot);
            draft.history.currentTransaction = null;
          });
          throw error;
        }
      },

      // ===== Utility Actions =====
      clearAll: () => {
        set((draft) => {
          // Clear nodes and arrows
          draft.nodes.clear();
          draft.arrows.clear();
          draft.diagramId = null;
          draft.diagramName = 'Untitled';
          draft.diagramDescription = '';
          draft.diagramFormat = null;
          draft.dataVersion = 0;

          // Clear execution
          draft.execution.id = null;
          draft.execution.isRunning = false;
          draft.execution.isPaused = false;
          draft.execution.runningNodes.clear();
          draft.execution.nodeStates.clear();
          draft.execution.context = {};

          // Clear persons
          draft.persons.clear();
          if ('dataVersion' in draft) {
            draft.dataVersion = 0;
          }

          // Clear handles
          draft.handles.clear();
          draft.handleIndex.clear();

          // Clear history
          draft.history.undoStack = [];
          draft.history.redoStack = [];
          draft.history.currentTransaction = null;

          // Reset UI
          draft.selectedId = null;
          draft.selectedType = null;
          draft.multiSelectedIds.clear();
          draft.highlightedPersonId = null;
        });
      },
    };
  };

  // ===== Apply Middleware Stack =====

  // Use explicit any type to avoid type instantiation depth errors with complex middleware chains
  // This is a known limitation with Zustand's middleware typing when combining immer, subscribeWithSelector, and devtools
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const withImmer = immer(storeCreator as any);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const withSelector = subscribeWithSelector(withImmer as any);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let store: any = withSelector;

  // Apply side effects middleware
  if (finalConfig.middleware?.length) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    store = sideEffectsMiddleware(store as any);
  }

  // Apply devtools in development
  if (finalConfig.enableDevtools) {
    store = devtools(store, {
      name: 'DiPeO Store',
      serialize: {
        replacer: (_key: string, value: unknown) => {
          // Handle Map serialization for devtools
          if (value instanceof Map) {
            return {
              _type: 'Map',
              _value: Array.from(value.entries()),
            };
          }
          return value;
        },
        reviver: (_key: string, value: unknown) => {
          // Handle Map deserialization from devtools
          if (value && typeof value === 'object' && '_type' in value) {
            if (value._type === 'Map' && '_value' in value) {
              return new Map(value._value as Array<[unknown, unknown]>);
            }
          }
          return value;
        },
      },
    });
  }

  return create<UnifiedStore>()(store);
}

// ===== Create and Export Store Instance =====

export const useUnifiedStore = createUnifiedStore();

// Register default side effects
if (typeof window !== 'undefined') {
  registerDefaultSideEffects();
}

// ===== Legacy Exports for Backward Compatibility =====

export const useStore = useUnifiedStore;

export const useNodeById = (nodeId: NodeID | null) =>
  useUnifiedStore((state) => nodeId ? state.nodes.get(nodeId) : null);

export const useArrowById = (arrowId: ArrowID | null) =>
  useUnifiedStore((state) => arrowId ? state.arrows.get(arrowId) : null);

export const usePersonById = (personId: PersonID | null) =>
  useUnifiedStore((state) => personId ? state.persons.get(personId) : null);

export const useNodes = () =>
  useUnifiedStore((state) => state.nodesArray);

export const useArrows = () =>
  useUnifiedStore((state) => state.arrowsArray);

export const usePersons = () =>
  useUnifiedStore((state) => state.personsArray);

export const useIsExecuting = () =>
  useUnifiedStore((state) => state.execution.isRunning);

// ===== Store Utilities =====

export function getStoreSnapshot(): StoreSnapshot {
  return createSnapshot(useUnifiedStore.getState());
}

export function loadStoreSnapshot(snapshot: StoreSnapshot): void {
  useUnifiedStore.setState((state) => {
    restoreSnapshot(state, snapshot);
    return state;
  });
}

export function resetStore(): void {
  useUnifiedStore.getState().clearAll();
}
