// Hook for history (undo/redo) actions
import { useCallback } from 'react';
import { 
  useUndo,
  useRedo,
  useCanUndo,
  useCanRedo,
  useNodes,
  useArrows,
  usePersons,
  useLoadDiagram
} from '../../common/utils/storeSelectors';
import { useHistoryStore } from '../stores';

export const useHistoryActions = () => {
  const { saveToHistory, clearHistory, initializeHistory } = useHistoryStore();
  const undo = useUndo();
  const redo = useRedo();
  const canUndo = useCanUndo();
  const canRedo = useCanRedo();
  const nodes = useNodes();
  const arrows = useArrows();
  const persons = usePersons();
  const loadDiagram = useLoadDiagram();

  // Save current state before making changes
  const saveCurrentState = useCallback(() => {
    saveToHistory({ nodes, arrows, persons });
  }, [nodes, arrows, persons, saveToHistory]);

  // Handle undo action
  const handleUndo = useCallback(() => {
    const previousState = undo();
    if (previousState) {
      // Update diagram
      loadDiagram({
        nodes: previousState.nodes,
        arrows: previousState.arrows,
        persons: previousState.persons,
        apiKeys: [] // Preserve existing API keys
      }, 'local');
    }
  }, [undo, loadDiagram]);

  // Handle redo action
  const handleRedo = useCallback(() => {
    const nextState = redo();
    if (nextState) {
      // Update diagram
      loadDiagram({
        nodes: nextState.nodes,
        arrows: nextState.arrows,
        persons: nextState.persons,
        apiKeys: [] // Preserve existing API keys
      }, 'local');
    }
  }, [redo, loadDiagram]);

  // Initialize history with current state
  const initHistory = useCallback(() => {
    initializeHistory({ nodes, arrows, persons });
  }, [nodes, arrows, persons, initializeHistory]);

  return {
    saveCurrentState,
    handleUndo,
    handleRedo,
    canUndo,
    canRedo,
    clearHistory,
    initHistory,
  };
};