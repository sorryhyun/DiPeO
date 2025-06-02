import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { DiagramState } from '@/shared/types';
import { sanitizeDiagram } from "@/serialization/utils/diagramSanitizer";
import { useNodeArrowStore } from './nodeArrowStore';
import { usePersonStore } from './personStore';
import { useApiKeyStore } from './apiKeyStore';

export interface DiagramOperationsState {
  clearDiagram: () => void;
  loadDiagram: (state: DiagramState) => void;
  exportDiagram: () => DiagramState;
}

export const useDiagramOperationsStore = create<DiagramOperationsState>()(
  devtools(
    () => ({
      clearDiagram: () => {
        // Clear all stores
        useNodeArrowStore.getState().clearNodesAndArrows();
        usePersonStore.getState().clearPersons();
        useApiKeyStore.getState().clearApiKeys();
      },
      
      loadDiagram: (state: DiagramState) => {
        const sanitized = sanitizeDiagram(state);
        
        // Load data into respective stores
        useNodeArrowStore.getState().setNodes(sanitized.nodes || []);
        useNodeArrowStore.getState().setArrows(sanitized.arrows || []);
        usePersonStore.getState().setPersons(sanitized.persons || []);
        useApiKeyStore.getState().setApiKeys(sanitized.apiKeys || []);
      },
      
      exportDiagram: (): DiagramState => {
        const nodeArrowState = useNodeArrowStore.getState();
        const personState = usePersonStore.getState();
        const apiKeyState = useApiKeyStore.getState();
        
        const diagram = sanitizeDiagram({
          nodes: nodeArrowState.nodes,
          arrows: nodeArrowState.arrows,
          persons: personState.persons,
          apiKeys: apiKeyState.apiKeys
        });
        
        return diagram;
      },
    }),
    {
      name: 'diagram-operations-store',
    }
  )
);