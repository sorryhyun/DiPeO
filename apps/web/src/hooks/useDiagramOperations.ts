/**
 * useDiagramOperations - Diagram operation utilities
 * 
 * This file contains utility functions for diagram operations.
 */

import { useUnifiedStore } from '@/hooks/useUnifiedStore';

/**
 * Clear all diagram data
 * This function clears all diagram elements and resets the selection.
 */
export const clearDiagram = () => {
  const state = useUnifiedStore.getState();
  
  state.transaction(() => {
    state.nodes.clear();
    state.arrows.clear();
    state.handles.clear();
    state.persons.clear();
    state.apiKeys.clear();
    state.clearSelection();
  });
};