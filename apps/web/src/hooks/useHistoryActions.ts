// Hook for history (undo/redo) actions
import { useCallback } from 'react';
import { useHistoryStore } from '@/stores';

export const useHistoryActions = () => {
  const { 
    undo,
    redo,
    canUndo,
    canRedo,
    saveToHistory,
    clearHistory,
    initializeHistory,
    setHistoryEnabled
  } = useHistoryStore();

  // Save current state before making changes
  const saveCurrentState = useCallback((action?: string) => {
    saveToHistory(action);
  }, [saveToHistory]);

  // Handle undo action
  const handleUndo = useCallback(() => {
    undo();
  }, [undo]);

  // Handle redo action
  const handleRedo = useCallback(() => {
    redo();
  }, [redo]);

  // Initialize history with current state
  const initHistory = useCallback(() => {
    initializeHistory();
  }, [initializeHistory]);

  return {
    saveCurrentState,
    handleUndo,
    handleRedo,
    canUndo,
    canRedo,
    clearHistory,
    initHistory,
    setHistoryEnabled
  };
};