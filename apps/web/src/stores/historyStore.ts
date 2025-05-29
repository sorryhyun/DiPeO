// History state store for undo/redo functionality
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Edge } from '@xyflow/react';
import { 
  ArrowData, PersonDefinition, DiagramNode
} from '@repo/core-model';

export interface HistoryState {
  nodes: DiagramNode[];
  arrows: Edge<ArrowData>[];
  persons: PersonDefinition[];
}

export interface HistoryStore {
  history: HistoryState[];
  historyIndex: number;
  maxHistorySize: number;

  // Actions
  saveToHistory: (state: HistoryState) => void;
  undo: () => HistoryState | null;
  redo: () => HistoryState | null;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clearHistory: () => void;
  initializeHistory: (state: HistoryState) => void;
}

export const useHistoryStore = create<HistoryStore>()(
  devtools(
    (set, get) => ({
      history: [],
      historyIndex: -1,
      maxHistorySize: 50,

      saveToHistory: (state) => {
        const { history, historyIndex, maxHistorySize } = get();
        
        // Remove any forward history if we're not at the end
        const newHistory = history.slice(0, historyIndex + 1);
        
        // Add current state (deep clone to prevent mutations)
        newHistory.push({
          nodes: JSON.parse(JSON.stringify(state.nodes)),
          arrows: JSON.parse(JSON.stringify(state.arrows)),
          persons: JSON.parse(JSON.stringify(state.persons)),
        });
        
        // Limit history size
        if (newHistory.length > maxHistorySize) {
          newHistory.shift();
        }
        
        set({
          history: newHistory,
          historyIndex: newHistory.length - 1,
        });
      },

      undo: () => {
        const { history, historyIndex } = get();
        if (historyIndex > 0) {
          const previousState = history[historyIndex - 1];
          set({ historyIndex: historyIndex - 1 });
          
          // Return deep clone to prevent mutations
          return {
            nodes: JSON.parse(JSON.stringify(previousState.nodes)),
            arrows: JSON.parse(JSON.stringify(previousState.arrows)),
            persons: JSON.parse(JSON.stringify(previousState.persons)),
          };
        }
        return null;
      },

      redo: () => {
        const { history, historyIndex } = get();
        if (historyIndex < history.length - 1) {
          const nextState = history[historyIndex + 1];
          set({ historyIndex: historyIndex + 1 });
          
          // Return deep clone to prevent mutations
          return {
            nodes: JSON.parse(JSON.stringify(nextState.nodes)),
            arrows: JSON.parse(JSON.stringify(nextState.arrows)),
            persons: JSON.parse(JSON.stringify(nextState.persons)),
          };
        }
        return null;
      },

      canUndo: () => {
        const { historyIndex } = get();
        return historyIndex > 0;
      },

      canRedo: () => {
        const { history, historyIndex } = get();
        return historyIndex < history.length - 1;
      },

      clearHistory: () => {
        set({
          history: [],
          historyIndex: -1,
        });
      },

      initializeHistory: (state) => {
        set({
          history: [{
            nodes: JSON.parse(JSON.stringify(state.nodes)),
            arrows: JSON.parse(JSON.stringify(state.arrows)),
            persons: JSON.parse(JSON.stringify(state.persons)),
          }],
          historyIndex: 0,
        });
      },
    }),
    {
      name: 'history-store',
    }
  )
);