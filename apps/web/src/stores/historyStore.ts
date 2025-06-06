import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { useDiagramStore } from './diagramStore';
import { Node, Arrow, Person, ApiKey } from '@/types';

interface DiagramSnapshot {
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
  timestamp: number;
}

export interface HistoryState {
  undoStack: DiagramSnapshot[];
  redoStack: DiagramSnapshot[];
  canUndo: boolean;
  canRedo: boolean;
  maxHistorySize: number;
  isHistoryEnabled: boolean;
  lastAction: string | null;
}

interface HistoryActions {
  undo: () => void;
  redo: () => void;
  saveToHistory: (action?: string) => void;
  clearHistory: () => void;
  initializeHistory: () => void;
  setHistoryEnabled: (enabled: boolean) => void;
}

export interface HistoryStore extends HistoryState, HistoryActions {}

const MAX_HISTORY_SIZE = 50;

function createSnapshot(): DiagramSnapshot {
  const state = useDiagramStore.getState();
  return {
    nodes: [...state.nodes],
    arrows: [...state.arrows],
    persons: [...state.persons],
    apiKeys: [...state.apiKeys],
    timestamp: Date.now()
  };
}

function restoreSnapshot(snapshot: DiagramSnapshot) {
  const diagramStore = useDiagramStore.getState();
  diagramStore.setNodes(snapshot.nodes);
  diagramStore.setArrows(snapshot.arrows);
  diagramStore.setPersons(snapshot.persons);
  diagramStore.setApiKeys(snapshot.apiKeys);
}

export const useHistoryStore = create<HistoryStore>()(
  devtools(
    (set, get) => ({
      // State
      undoStack: [],
      redoStack: [],
      canUndo: false,
      canRedo: false,
      maxHistorySize: MAX_HISTORY_SIZE,
      isHistoryEnabled: true,
      lastAction: null,

      // Actions
      undo: () => {
        const { undoStack, redoStack, isHistoryEnabled } = get();
        
        if (!isHistoryEnabled || undoStack.length === 0) return;

        // Save current state to redo stack before undoing
        const currentSnapshot = createSnapshot();
        
        // Pop from undo stack
        const newUndoStack = undoStack.slice(0, -1);
        
        // Restore the previous state
        if (newUndoStack.length > 0) {
          const previousSnapshot = newUndoStack[newUndoStack.length - 1];
          if (previousSnapshot) {
            restoreSnapshot(previousSnapshot);
          }
        } else {
          // If no more states in undo stack, restore to empty state
          const diagramStore = useDiagramStore.getState();
          diagramStore.clear();
        }
        
        // Update stacks
        set({
          undoStack: newUndoStack,
          redoStack: [...redoStack, currentSnapshot],
          canUndo: newUndoStack.length > 0,
          canRedo: true,
          lastAction: 'undo'
        });
      },

      redo: () => {
        const { undoStack, redoStack, isHistoryEnabled } = get();
        
        if (!isHistoryEnabled || redoStack.length === 0) return;

        // Save current state to undo stack before redoing
        const currentSnapshot = createSnapshot();
        
        // Pop from redo stack
        const nextSnapshot = redoStack[redoStack.length - 1];
        if (!nextSnapshot) return;
        
        const newRedoStack = redoStack.slice(0, -1);
        
        // Restore the next state
        restoreSnapshot(nextSnapshot);
        
        // Update stacks
        set({
          undoStack: [...undoStack, currentSnapshot],
          redoStack: newRedoStack,
          canUndo: true,
          canRedo: newRedoStack.length > 0,
          lastAction: 'redo'
        });
      },

      saveToHistory: (action?: string) => {
        const { undoStack, maxHistorySize, isHistoryEnabled, lastAction } = get();
        
        if (!isHistoryEnabled) return;
        
        // Skip saving if this is called as part of undo/redo
        if (lastAction === 'undo' || lastAction === 'redo') {
          set({ lastAction: null });
          return;
        }

        const snapshot = createSnapshot();
        
        // Don't save if nothing changed
        if (undoStack.length > 0) {
          const lastSnapshot = undoStack[undoStack.length - 1];
          if (lastSnapshot && 
            JSON.stringify(lastSnapshot.nodes) === JSON.stringify(snapshot.nodes) &&
            JSON.stringify(lastSnapshot.arrows) === JSON.stringify(snapshot.arrows) &&
            JSON.stringify(lastSnapshot.persons) === JSON.stringify(snapshot.persons) &&
            JSON.stringify(lastSnapshot.apiKeys) === JSON.stringify(snapshot.apiKeys)
          ) {
            return;
          }
        }

        // Add to undo stack
        let newUndoStack = [...undoStack, snapshot];
        
        // Limit stack size
        if (newUndoStack.length > maxHistorySize) {
          newUndoStack = newUndoStack.slice(-maxHistorySize);
        }
        
        // Clear redo stack when new action is performed
        set({
          undoStack: newUndoStack,
          redoStack: [],
          canUndo: newUndoStack.length > 0,
          canRedo: false,
          lastAction: action || null
        });
      },

      clearHistory: () => {
        set({
          undoStack: [],
          redoStack: [],
          canUndo: false,
          canRedo: false,
          lastAction: null
        });
      },

      initializeHistory: () => {
        const { saveToHistory, clearHistory } = get();
        clearHistory();
        
        // Save initial state
        setTimeout(() => {
          saveToHistory('initial');
        }, 100);
      },

      setHistoryEnabled: (enabled: boolean) => {
        set({ isHistoryEnabled: enabled });
      }
    }),
    { name: 'history-store' }
  )
);