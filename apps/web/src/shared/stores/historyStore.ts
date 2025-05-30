// History state store for undo/redo functionality using Immer patches
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { 
  produceWithPatches, applyPatches, enablePatches, Patch
} from 'immer';
import { 
  PersonDefinition, DiagramNode, Arrow
} from '../types';

// Enable Immer patches feature
enablePatches();

export interface HistoryState {
  nodes: DiagramNode[];
  arrows: Arrow[];
  persons: PersonDefinition[];
}

interface HistoryEntry {
  patches: Patch[];
  inversePatches: Patch[];
  timestamp: number;
  description?: string;
}

export interface HistoryStore {
  // The base state at the start of history
  baseState: HistoryState | null;
  
  // Array of patches to get from baseState to current
  history: HistoryEntry[];
  
  // Current position in history (-1 means at latest)
  historyIndex: number;
  
  // Configuration
  maxHistorySize: number;
  compressionThreshold: number;
  
  // Actions
  saveToHistory: (state: HistoryState) => void;
  undo: () => HistoryState | null;
  redo: () => HistoryState | null;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clearHistory: () => void;
  initializeHistory: (state: HistoryState) => void;
  
  // Internal helpers
  _saveWithPrevious: (prevState: HistoryState, nextState: HistoryState, description?: string) => void;
  _compress: () => void;
  _getCurrentState: () => HistoryState | null;
}

// Track previous state internally
let previousState: HistoryState | null = null;

export const useHistoryStore = create<HistoryStore>()(
  devtools(
    (set, get) => ({
      baseState: null,
      history: [],
      historyIndex: -1,
      maxHistorySize: 100,
      compressionThreshold: 50,

      saveToHistory: (state) => {
        const { _saveWithPrevious, initializeHistory } = get();
        
        if (previousState) {
          _saveWithPrevious(previousState, state, 'User action');
        } else {
          // First save, initialize the history
          initializeHistory(state);
        }
        
        // Update our reference to the current state
        previousState = state;
      },

      _saveWithPrevious: (prevState, nextState, description) => {
        const { history, historyIndex, maxHistorySize, compressionThreshold } = get();
        
        // Calculate patches between states
        const [, patches, inversePatches] = produceWithPatches(
          prevState,
          draft => {
            // Apply the differences
            draft.nodes = nextState.nodes;
            draft.arrows = nextState.arrows;
            draft.persons = nextState.persons;
          }
        );
        
        // Don't save if no changes
        if (patches.length === 0) return;
        
        // Remove any forward history if we're not at the end
        const newHistory = history.slice(0, historyIndex + 1);
        
        // Add new entry
        const entry: HistoryEntry = {
          patches,
          inversePatches,
          timestamp: Date.now(),
          description
        };
        
        newHistory.push(entry);
        
        // Check if we need to compress
        if (newHistory.length > compressionThreshold) {
          setTimeout(() => get()._compress(), 0);
          return;
        }
        
        // Limit history size
        if (newHistory.length > maxHistorySize) {
          const toRemove = newHistory.length - maxHistorySize;
          newHistory.splice(0, toRemove);
        }
        
        set({
          history: newHistory,
          historyIndex: newHistory.length - 1,
          baseState: get().baseState || prevState
        });
      },

      undo: () => {
        const { baseState, history, historyIndex } = get();
        
        if (!baseState || historyIndex < 0) return null;
        
        // Reconstruct state at historyIndex - 1
        let currentState = baseState;
        
        // Apply patches up to historyIndex - 1
        for (let i = 0; i < historyIndex; i++) {
          currentState = applyPatches(currentState, history[i].patches);
        }
        
        set({ historyIndex: historyIndex - 1 });
        previousState = currentState;
        return currentState;
      },

      redo: () => {
        const { baseState, history, historyIndex } = get();
        
        if (!baseState || historyIndex >= history.length - 1) return null;
        
        // Reconstruct state at historyIndex + 1
        let currentState = baseState;
        
        // Apply patches up to historyIndex + 1
        for (let i = 0; i <= historyIndex + 1; i++) {
          currentState = applyPatches(currentState, history[i].patches);
        }
        
        set({ historyIndex: historyIndex + 1 });
        previousState = currentState;
        return currentState;
      },

      _compress: () => {
        const { baseState, history, historyIndex } = get();
        if (!baseState || history.length === 0) return;
        
        // Reconstruct current state
        let currentState = baseState;
        for (let i = 0; i <= historyIndex; i++) {
          currentState = applyPatches(currentState, history[i].patches);
        }
        
        // Make current state the new base
        set({
          baseState: currentState,
          history: [],
          historyIndex: -1
        });
        
        console.info('[History] Compressed history, created new snapshot');
      },

      _getCurrentState: () => {
        const { baseState, history, historyIndex } = get();
        
        if (!baseState) return null;
        
        let currentState = baseState;
        for (let i = 0; i <= historyIndex; i++) {
          currentState = applyPatches(currentState, history[i].patches);
        }
        
        return currentState;
      },

      canUndo: () => get().historyIndex >= 0,
      
      canRedo: () => {
        const { history, historyIndex } = get();
        return historyIndex < history.length - 1;
      },

      clearHistory: () => {
        previousState = null;
        set({
          baseState: null,
          history: [],
          historyIndex: -1
        });
      },

      initializeHistory: (state) => {
        previousState = state;
        set({
          baseState: state,
          history: [],
          historyIndex: -1
        });
      },
    }),
    {
      name: 'history-store',
    }
  )
);