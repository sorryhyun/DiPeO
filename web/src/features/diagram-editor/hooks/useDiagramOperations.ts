// Clear all diagram data

import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';

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