import { DiagramState } from '@/common/types';
import { useDiagramStore } from '@/state/stores/diagramStore';

// Utility functions for diagram operations
export const exportDiagram = (): DiagramState => {
  return useDiagramStore.getState().exportDiagram();
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
    exportDiagram: () => store.exportDiagram(),
    loadDiagram: (diagram: DiagramState, source: 'local' | 'external' = 'local') => {
      store.loadDiagram(diagram, source);
    },
    clearDiagram: () => {
      store.clearDiagram();
    }
  };
};