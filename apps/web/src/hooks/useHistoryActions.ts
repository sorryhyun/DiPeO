// Hook for history (undo/redo) actions
import { useCallback } from 'react';
import { useHistoryStore, useConsolidatedDiagramStore } from '@/stores';

export const useHistoryActions = () => {
  const { undo, redo, canUndo, canRedo, saveToHistory, clearHistory, initializeHistory } = useHistoryStore();
  const { nodes, arrows, persons, loadDiagram } = useConsolidatedDiagramStore();

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
      });
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
      });
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
    canUndo: canUndo(),
    canRedo: canRedo(),
    clearHistory,
    initHistory,
  };
};