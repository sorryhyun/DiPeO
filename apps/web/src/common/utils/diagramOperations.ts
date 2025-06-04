import { DiagramState } from '@/common/types';
import { useDiagramStore } from '@/state/stores/diagramStore';

// Utility functions for diagram operations
export const exportDiagram = (): DiagramState => {
  const state = useDiagramStore.getState();
  return {
    nodes: state.nodes,
    arrows: state.arrows,
    persons: state.persons,
    apiKeys: state.apiKeys
  };
};

export const loadDiagram = (diagram: DiagramState, source: 'local' | 'external' = 'local') => {
  useDiagramStore.getState().loadDiagram(diagram, source);
};

export const clearDiagram = () => {
  useDiagramStore.getState().clearDiagram();
};

// Hook for reactive diagram operations
export const useDiagramOperations = () => {
  const store = useDiagramStore();
  
  return {
    exportDiagram: () => ({
      nodes: store.nodes,
      arrows: store.arrows,
      persons: store.persons,
      apiKeys: store.apiKeys
    }),
    loadDiagram: (diagram: DiagramState, source: 'local' | 'external' = 'local') => {
      store.loadDiagram(diagram, source);
    },
    clearDiagram: () => {
      store.clearDiagram();
    }
  };
};