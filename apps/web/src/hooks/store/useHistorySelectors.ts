import React from 'react';
import { useHistoryStore } from '@/stores/historyStore';

export const useHistorySelectors = () => {
  const canUndo = useHistoryStore(state => state.canUndo);
  const canRedo = useHistoryStore(state => state.canRedo);
  const undo = useHistoryStore(state => state.undo);
  const redo = useHistoryStore(state => state.redo);
  
  return React.useMemo(() => ({
    canUndo,
    canRedo,
    undo,
    redo,
  }), [canUndo, canRedo, undo, redo]);
};