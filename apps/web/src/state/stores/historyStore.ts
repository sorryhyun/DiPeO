import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface HistoryState {
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
}

export interface HistoryStore extends HistoryState {
  saveToHistory: () => void;
  clearHistory: () => void;
  initializeHistory: () => void;
}

export const useHistoryStore = create<HistoryStore>()(
  devtools(
    (set) => ({
      canUndo: false,
      canRedo: false,
      undo: () => console.log('Undo not implemented'),
      redo: () => console.log('Redo not implemented'),
      saveToHistory: () => console.log('Save to history not implemented'),
      clearHistory: () => console.log('Clear history not implemented'),
      initializeHistory: () => console.log('Initialize history not implemented')
    }),
    { name: 'history-store' }
  )
);