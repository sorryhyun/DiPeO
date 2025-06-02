import { create } from 'zustand';
import { persist, devtools, subscribeWithSelector } from 'zustand/middleware';
import { OnNodesChange, OnConnect } from '@xyflow/react';
import {
  DiagramState, PersonDefinition, ApiKey, DiagramNode,
  OnArrowsChange, Arrow, ArrowData
} from '@/shared/types';
import { useNodeArrowStore } from '@/core/stores/nodeArrowStore';
import { usePersonStore } from '@/core/stores/personStore';
import { useApiKeyStore } from '@/core/stores/apiKeyStore';
import { useMonitorStore } from '@/core/stores/monitorStore';
import { useDiagramOperationsStore } from '@/core/stores/diagramOperationsStore';

export interface ConsolidatedDiagramState {
  // Node and Arrow state (from nodeArrowStore)
  nodes: DiagramNode[];
  arrows: Arrow[];
  onNodesChange: OnNodesChange;
  onArrowsChange: OnArrowsChange;
  onConnect: OnConnect;
  addNode: (type: string, position: { x: number; y: number }) => void;
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void;
  deleteNode: (nodeId: string) => void;
  updateArrowData: (arrowId: string, data: Partial<ArrowData>) => void;
  deleteArrow: (arrowId: string) => void;
  
  // Person state (from personStore)
  persons: PersonDefinition[];
  addPerson: (person: Omit<PersonDefinition, 'id'>) => void;
  updatePerson: (personId: string, data: Partial<PersonDefinition>) => void;
  deletePerson: (personId: string) => void;
  getPersonById: (personId: string) => PersonDefinition | undefined;
  clearPersons: () => void;
  
  // API Key state (from apiKeyStore)
  apiKeys: ApiKey[];
  addApiKey: (apiKey: Omit<ApiKey, 'id'>) => void;
  updateApiKey: (apiKeyId: string, apiKeyData: Partial<ApiKey>) => void;
  deleteApiKey: (apiKeyId: string) => void;
  getApiKeyById: (apiKeyId: string) => ApiKey | undefined;
  clearApiKeys: () => void;
  loadApiKeys: () => Promise<void>;
  
  // Monitor state (from monitorStore)
  monitorNodes: DiagramNode[];
  monitorArrows: Arrow[];
  monitorPersons: PersonDefinition[];
  monitorApiKeys: ApiKey[];
  isMonitorMode: boolean;
  loadMonitorDiagram: (state: DiagramState) => void;
  clearMonitorDiagram: () => void;
  setMonitorMode: (enabled: boolean) => void;
  exportMonitorDiagram: () => DiagramState;
  
  // Diagram operations (from diagramOperationsStore)
  clearDiagram: () => void;
  loadDiagram: (state: DiagramState) => void;
  exportDiagram: () => DiagramState;
}

// Create a facade that delegates to individual stores
export const useConsolidatedDiagramStore = create<ConsolidatedDiagramState>()(
  devtools(
    subscribeWithSelector(
      persist(
        (_set) => ({
          // Node and Arrow state - subscribe to nodeArrowStore
          nodes: [],
          arrows: [],
          onNodesChange: (changes) => useNodeArrowStore.getState().onNodesChange(changes),
          onArrowsChange: (changes) => useNodeArrowStore.getState().onArrowsChange(changes),
          onConnect: (connection) => useNodeArrowStore.getState().onConnect(connection),
          addNode: (type, position) => useNodeArrowStore.getState().addNode(type, position),
          updateNodeData: (nodeId, data) => useNodeArrowStore.getState().updateNodeData(nodeId, data),
          deleteNode: (nodeId) => useNodeArrowStore.getState().deleteNode(nodeId),
          updateArrowData: (arrowId, data) => useNodeArrowStore.getState().updateArrowData(arrowId, data),
          deleteArrow: (arrowId) => useNodeArrowStore.getState().deleteArrow(arrowId),
          
          // Person state - subscribe to personStore
          persons: [],
          addPerson: (person) => usePersonStore.getState().addPerson(person),
          updatePerson: (personId, data) => usePersonStore.getState().updatePerson(personId, data),
          deletePerson: (personId) => usePersonStore.getState().deletePerson(personId),
          getPersonById: (personId) => {
            // Check monitor mode directly from monitorStore to avoid circular reference
            const monitorState = useMonitorStore.getState();
            if (monitorState.isMonitorMode) {
              return monitorState.monitorPersons.find(p => p.id === personId);
            }
            return usePersonStore.getState().getPersonById(personId);
          },
          clearPersons: () => usePersonStore.getState().clearPersons(),
          
          // API Key state - subscribe to apiKeyStore
          apiKeys: [],
          addApiKey: (apiKey) => useApiKeyStore.getState().addApiKey(apiKey),
          updateApiKey: (apiKeyId, apiKeyData) => useApiKeyStore.getState().updateApiKey(apiKeyId, apiKeyData),
          deleteApiKey: (apiKeyId) => useApiKeyStore.getState().deleteApiKey(apiKeyId),
          getApiKeyById: (apiKeyId) => useApiKeyStore.getState().getApiKeyById(apiKeyId),
          clearApiKeys: () => useApiKeyStore.getState().clearApiKeys(),
          loadApiKeys: () => useApiKeyStore.getState().loadApiKeys(),
          
          // Monitor state - subscribe to monitorStore
          monitorNodes: [],
          monitorArrows: [],
          monitorPersons: [],
          monitorApiKeys: [],
          isMonitorMode: false,
          loadMonitorDiagram: (state) => useMonitorStore.getState().loadMonitorDiagram(state),
          clearMonitorDiagram: () => useMonitorStore.getState().clearMonitorDiagram(),
          setMonitorMode: (enabled) => useMonitorStore.getState().setMonitorMode(enabled),
          exportMonitorDiagram: () => useMonitorStore.getState().exportMonitorDiagram(),
          
          // Diagram operations
          clearDiagram: () => useDiagramOperationsStore.getState().clearDiagram(),
          loadDiagram: (state) => useDiagramOperationsStore.getState().loadDiagram(state),
          exportDiagram: () => useDiagramOperationsStore.getState().exportDiagram(),
        }),
        {
          name: 'consolidated-diagram-store',
          partialize: () => ({}), // Don't persist anything - individual stores handle their own persistence
        }
      )
    ),
    {
      name: 'consolidated-diagram-store',
    }
  )
);

// Subscribe to individual stores and update consolidated store
// This ensures the facade stays in sync with the underlying stores
useNodeArrowStore.subscribe(
  (state) => ({ nodes: state.nodes, arrows: state.arrows }),
  (newState) => {
    useConsolidatedDiagramStore.setState({
      nodes: newState.nodes,
      arrows: newState.arrows,
    });
  }
);

usePersonStore.subscribe(
  (state) => ({ persons: state.persons }),
  (newState) => {
    useConsolidatedDiagramStore.setState({
      persons: newState.persons,
    });
  }
);

useApiKeyStore.subscribe(
  (state) => ({ apiKeys: state.apiKeys }),
  (newState) => {
    useConsolidatedDiagramStore.setState({
      apiKeys: newState.apiKeys,
    });
  }
);

useMonitorStore.subscribe(
  (state) => ({
    monitorNodes: state.monitorNodes,
    monitorArrows: state.monitorArrows,
    monitorPersons: state.monitorPersons,
    monitorApiKeys: state.monitorApiKeys,
    isMonitorMode: state.isMonitorMode,
  }),
  (newState) => {
    useConsolidatedDiagramStore.setState({
      monitorNodes: newState.monitorNodes,
      monitorArrows: newState.monitorArrows,
      monitorPersons: newState.monitorPersons,
      monitorApiKeys: newState.monitorApiKeys,
      isMonitorMode: newState.isMonitorMode,
    });
  }
);