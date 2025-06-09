import { createWithEqualityFn } from 'zustand/traditional';
import { devtools } from 'zustand/middleware';
import { DiagramCanvasStore } from './diagramCanvasStore';
import {DomainNode, DomainArrow, DomainPerson, DomainApiKey} from '@/types';

interface DiagramSnapshot {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  apiKeys: DomainApiKey[];
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
  diagramStore: DiagramCanvasStore | null;
}

interface HistoryActions {
  setDiagramStore: (store: DiagramCanvasStore) => void;
  undo: () => void;
  redo: () => void;
  saveToHistory: (action?: string) => void;
  clearHistory: () => void;
  initializeHistory: () => void;
  setHistoryEnabled: (enabled: boolean) => void;
}

export interface HistoryStore extends HistoryState, HistoryActions {}

const MAX_HISTORY_SIZE = 50;

function createSnapshot(store: DiagramCanvasStore): DiagramSnapshot {
  return {
    nodes: store.getAllNodes(),
    arrows: store.getAllArrows(),
    persons: store.getAllPersons(),
    apiKeys: store.getAllApiKeys(),
    timestamp: Date.now()
  };
}

function restoreSnapshot(snapshot: DiagramSnapshot, store: DiagramCanvasStore) {
  // Clear existing data
  store.clear();
  
  // Restore entities in order
  snapshot.apiKeys.forEach(apiKey => store.addApiKey(apiKey));
  snapshot.persons.forEach(person => store.addPerson(person));
  snapshot.nodes.forEach(node => store.addNode(node));
  snapshot.arrows.forEach(arrow => store.addArrow(arrow));
}

export const useHistoryStore = createWithEqualityFn<HistoryStore>()(
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
      diagramStore: null,

      // Actions
      setDiagramStore: (store: DiagramCanvasStore) => {
        set({ diagramStore: store });
      },

      undo: () => {
        const { undoStack, redoStack, isHistoryEnabled, diagramStore } = get();
        
        if (!isHistoryEnabled || undoStack.length === 0 || !diagramStore) return;

        // Save current state to redo stack before undoing
        const currentSnapshot = createSnapshot(diagramStore);
        
        // Pop from undo stack
        const newUndoStack = undoStack.slice(0, -1);
        
        // Restore the previous state
        if (newUndoStack.length > 0) {
          const previousSnapshot = newUndoStack[newUndoStack.length - 1];
          if (previousSnapshot) {
            restoreSnapshot(previousSnapshot, diagramStore);
          }
        } else {
          // If no more states in undo stack, restore to empty state
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
        const { undoStack, redoStack, isHistoryEnabled, diagramStore } = get();
        
        if (!isHistoryEnabled || redoStack.length === 0 || !diagramStore) return;

        // Save current state to undo stack before redoing
        const currentSnapshot = createSnapshot(diagramStore);
        
        // Pop from redo stack
        const nextSnapshot = redoStack[redoStack.length - 1];
        if (!nextSnapshot) return;
        
        const newRedoStack = redoStack.slice(0, -1);
        
        // Restore the next state
        restoreSnapshot(nextSnapshot, diagramStore);
        
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
        const { undoStack, maxHistorySize, isHistoryEnabled, lastAction, diagramStore } = get();
        
        if (!isHistoryEnabled || !diagramStore) return;
        
        // Skip saving if this is called as part of undo/redo
        if (lastAction === 'undo' || lastAction === 'redo') {
          set({ lastAction: null });
          return;
        }

        const snapshot = createSnapshot(diagramStore);
        
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