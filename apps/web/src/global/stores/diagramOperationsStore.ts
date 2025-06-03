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
        console.log('loadDiagram: Input state', state);
        const sanitized = sanitizeDiagram(state);
        console.log('loadDiagram: Sanitized state', sanitized);
        
        // Load data into respective stores
        console.log('loadDiagram: Setting nodes', sanitized.nodes);
        useNodeArrowStore.getState().setNodes(sanitized.nodes || []);
        console.log('loadDiagram: Setting arrows', sanitized.arrows);
        useNodeArrowStore.getState().setArrows(sanitized.arrows || []);
        console.log('loadDiagram: Setting persons', sanitized.persons);
        usePersonStore.getState().setPersons(sanitized.persons || []);
        console.log('loadDiagram: Setting apiKeys', sanitized.apiKeys);
        useApiKeyStore.getState().setApiKeys(sanitized.apiKeys || []);
        console.log('loadDiagram: Complete');
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