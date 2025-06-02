import { create } from 'zustand';
import { persist, devtools, subscribeWithSelector } from 'zustand/middleware';
import {
  OnNodesChange, OnConnect,
  applyNodeChanges, Connection
} from '@xyflow/react';
import { nanoid } from 'nanoid';
import {
  ArrowData, DiagramState, PersonDefinition, ApiKey, DiagramNode, DiagramNodeData,
  getReactFlowType, OnArrowsChange, Arrow, applyArrowChanges, addArrow,
  StartBlockData, PersonJobBlockData, DBBlockData, JobBlockData,
  ConditionBlockData, EndpointBlockData, createErrorHandlerFactory
} from '@/shared/types';
import { sanitizeDiagram } from "@/serialization/utils/diagramSanitizer";
import { createPersonCrudActions, createApiKeyCrudActions } from "@/shared/utils/storeCrudUtils";
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';
import { toast } from 'sonner';


export interface ConsolidatedDiagramState {
  nodes: DiagramNode[];
  arrows: Arrow[];
  persons: PersonDefinition[];
  apiKeys: ApiKey[];
  
  // Monitor storage for external diagrams (not persisted)
  monitorNodes: DiagramNode[];
  monitorArrows: Arrow[];
  monitorPersons: PersonDefinition[];
  monitorApiKeys: ApiKey[];
  isMonitorMode: boolean;

  onNodesChange: OnNodesChange;
  onArrowsChange: OnArrowsChange;
  onConnect: OnConnect;
  addNode: (type: string, position: { x: number; y: number }) => void;
  updateNodeData: (nodeId: string, data: Record<string, any>) => void;
  deleteNode: (nodeId: string) => void;
  updateArrowData: (arrowId: string, data: Partial<ArrowData>) => void;
  deleteArrow: (arrowId: string) => void;

  addPerson: (person: Omit<PersonDefinition, 'id'>) => void;
  updatePerson: (personId: string, data: Partial<PersonDefinition>) => void;
  deletePerson: (personId: string) => void;
  getPersonById: (personId: string) => PersonDefinition | undefined;
  clearPersons: () => void;

  addApiKey: (apiKey: Omit<ApiKey, 'id'>) => void;
  updateApiKey: (apiKeyId: string, apiKeyData: Partial<ApiKey>) => void;
  deleteApiKey: (apiKeyId: string) => void;
  getApiKeyById: (apiKeyId: string) => ApiKey | undefined;
  clearApiKeys: () => void;
  loadApiKeys: () => Promise<void>;

  clearDiagram: () => void;
  loadDiagram: (state: DiagramState) => void;
  exportDiagram: () => DiagramState;
  
  // Monitor-specific methods
  loadMonitorDiagram: (state: DiagramState) => void;
  clearMonitorDiagram: () => void;
  setMonitorMode: (enabled: boolean) => void;
  exportMonitorDiagram: () => DiagramState;
}

const createErrorHandler = createErrorHandlerFactory(toast);

export const useConsolidatedDiagramStore = create<ConsolidatedDiagramState>()(
  devtools(
    subscribeWithSelector(
      persist(
        (set, get) => ({
        nodes: [],
        arrows: [],
        persons: [],
        apiKeys: [],
        
        // Monitor storage (not persisted)
        monitorNodes: [],
        monitorArrows: [],
        monitorPersons: [],
        monitorApiKeys: [],
        isMonitorMode: false,

        onNodesChange: (changes) => {
          set({ nodes: applyNodeChanges(changes, get().nodes) as DiagramNode[] });
        },

        onArrowsChange: (changes) => {
          set({ arrows: applyArrowChanges(changes, get().arrows) as Arrow<ArrowData>[] });
        },

        onConnect: (connection: Connection) => {
          const arrowId = `arrow-${nanoid().slice(0, 6)}`;
          const newArrow: Arrow = {
            id: arrowId,
            source: connection.source!,
            target: connection.target!,
            sourceHandle: connection.sourceHandle,
            targetHandle: connection.targetHandle,
            type: 'customArrow',
            data: { 
              id: arrowId,
              sourceBlockId: connection.source!,
              targetBlockId: connection.target!,
              kind: 'ALL' as const,
              template: '',
              conversationState: false,
              label: 'New Arrow'
            }
          };
          set({ arrows: addArrow(newArrow, get().arrows) });
        },

        addNode: (type: string, position: { x: number; y: number }) => {
          const reactFlowType = getReactFlowType(type);
          const nodeId = `${reactFlowType}-${nanoid().slice(0, 6)}`;
          type BlockData = StartBlockData | PersonJobBlockData | DBBlockData | JobBlockData | ConditionBlockData | EndpointBlockData;
          let nodeData: BlockData;

          // Set default data based on node type with proper interfaces
          switch (type) {
            case 'start':
              nodeData = { 
                id: nodeId,
                type: 'start',
                label: 'Start', 
                description: '' 
              };
              break;
            case 'person_job':
              nodeData = { 
                id: nodeId,
                type: 'person_job',
                label: 'Person Job', 
                prompt: '', 
                personId: undefined,
                description: ''
              };
              break;
            case 'job':
              nodeData = { 
                id: nodeId,
                type: 'job',
                subType: 'code',
                sourceDetails: '',
                label: 'Job', 
                description: '' 
              };
              break;
            case 'condition':
              nodeData = { 
                id: nodeId,
                type: 'condition',
                conditionType: 'expression',
                label: 'Condition', 
                expression: ''
              };
              break;
            case 'db':
              nodeData = { 
                id: nodeId,
                type: 'db',
                subType: 'fixed_prompt',
                sourceDetails: '',
                label: 'DB', 
                description: ''
              };
              break;
            case 'endpoint':
              nodeData = { 
                id: nodeId,
                type: 'endpoint',
                label: 'Endpoint', 
                description: '',
                saveToFile: false,
                filePath: '',
                fileFormat: 'json'
              };
              break;
            default:
              // Default to start node for unknown types
              nodeData = {
                id: nodeId,
                type: 'start',
                label: 'Unknown'
              };
          }

          const newNode: DiagramNode = {
            id: nodeId,
            type : reactFlowType,
            position,
            data: nodeData,
          };

          set({ nodes: [...get().nodes, newNode] });
        },

        updateNodeData: (nodeId: string, data: Record<string, unknown>) => {
          set({
            nodes: get().nodes.map(node =>
              node.id === nodeId ? { ...node, data: { ...node.data, ...data } as DiagramNodeData } : node
            )
          });
        },

        deleteNode: (nodeId: string) => {
          set({
            nodes: get().nodes.filter(node => node.id !== nodeId),
            arrows: get().arrows.filter(arrow => 
              arrow.source !== nodeId && arrow.target !== nodeId
            )
          });
        },

        updateArrowData: (arrowId: string, data: Partial<ArrowData>) => {
          set({
            arrows: get().arrows.map(arrow =>
              arrow.id === arrowId ? { 
                ...arrow, 
                data: { ...arrow.data, ...data } as ArrowData 
              } : arrow
            )
          });
        },

        deleteArrow: (arrowId: string) => {
          set({
            arrows: get().arrows.filter(arrow => arrow.id !== arrowId)
          });
        },

        // Person operations using generic CRUD
        ...createPersonCrudActions<PersonDefinition>(
          () => get().persons,
          (persons) => set({ persons }),
          'PERSON'
        ),

        // API key operations using generic CRUD
        ...createApiKeyCrudActions<ApiKey>(
          () => get().apiKeys,
          (apiKeys) => set({ apiKeys }),
          'APIKEY'
        ),

        loadApiKeys: async () => {
          const errorHandler = createErrorHandler('Load API Keys');
          try {
            const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
            if (!response.ok) {
              throw new Error(`Failed to load API keys: ${response.statusText}`);
            }
            
            const data = await response.json();
            const apiKeys = (Array.isArray(data) ? data : data.apiKeys || []).map((key: {id: string; name: string; service: string}) => ({
              id: key.id,
              name: key.name,
              service: key.service,
              keyReference: '***hidden***' // Don't store raw keys in frontend
            }));
            
            set({ apiKeys });
          } catch (error) {
            console.error('Error loading API keys:', error);
            errorHandler(error as Error);
            throw error;
          }
        },

        // Utility operations
        clearDiagram: () => {
          set({ 
            nodes: [], 
            arrows: [], 
            persons: [], 
            apiKeys: [] 
          });
        },

        loadDiagram: (state: DiagramState) => {
          const sanitized = sanitizeDiagram(state);
          set({
            nodes: (sanitized.nodes || []) as DiagramNode[],
            arrows: (sanitized.arrows || []) as Arrow[],
            persons: sanitized.persons || [],
            apiKeys: sanitized.apiKeys || []
          });
        },
        
        loadMonitorDiagram: (state: DiagramState) => {
          const sanitized = sanitizeDiagram(state);
          set({
            monitorNodes: (sanitized.nodes || []) as DiagramNode[],
            monitorArrows: (sanitized.arrows || []) as Arrow[],
            monitorPersons: sanitized.persons || [],
            monitorApiKeys: sanitized.apiKeys || [],
            isMonitorMode: true
          });
        },
        
        clearMonitorDiagram: () => {
          set({
            monitorNodes: [],
            monitorArrows: [],
            monitorPersons: [],
            monitorApiKeys: [],
            isMonitorMode: false
          });
        },
        
        setMonitorMode: (enabled: boolean) => {
          set({ isMonitorMode: enabled });
        },
        
        exportMonitorDiagram: (): DiagramState => {
          const { monitorNodes, monitorArrows, monitorPersons, monitorApiKeys } = get();
          const sanitized = sanitizeDiagram({
            nodes: monitorNodes,
            arrows: monitorArrows,
            persons: monitorPersons,
            apiKeys: monitorApiKeys
          });
          return sanitized;
        },

        exportDiagram: (): DiagramState => {
          const { nodes, arrows, persons, apiKeys } = sanitizeDiagram(get());
          return { nodes, arrows, persons, apiKeys };
        },

        }),
        {
          name: 'consolidated-diagram-store',
          partialize: (state) => ({
            nodes: state.nodes,
            arrows: state.arrows,
            persons: state.persons,
            apiKeys: state.apiKeys
          }),
        }
      )
    ),
    {
      name: 'consolidated-diagram-store',
    }
  )
);