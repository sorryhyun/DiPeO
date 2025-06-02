import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import {
  OnNodesChange, OnConnect,
  applyNodeChanges, Connection
} from '@xyflow/react';
import { nanoid } from 'nanoid';
import {
  ArrowData, DiagramNode, DiagramNodeData,
  getReactFlowType, OnArrowsChange, Arrow, applyArrowChanges, addArrow,
  StartBlockData, PersonJobBlockData, DBBlockData, JobBlockData,
  ConditionBlockData, EndpointBlockData
} from '@/shared/types';

export interface NodeArrowState {
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
  
  // Batch operations
  setNodes: (nodes: DiagramNode[]) => void;
  setArrows: (arrows: Arrow[]) => void;
  clearNodesAndArrows: () => void;
}

export const useNodeArrowStore = create<NodeArrowState>()(
  devtools(
    subscribeWithSelector(
      (set, get) => ({
        nodes: [],
        arrows: [],

        onNodesChange: (changes) => {
          set({ nodes: applyNodeChanges(changes, get().nodes) as DiagramNode[] });
        },

        onArrowsChange: (changes) => {
          set({ arrows: applyArrowChanges(changes, get().arrows) as Arrow<ArrowData>[] });
        },

        onConnect: (connection: Connection) => {
          const arrowId = `arrow-${nanoid().slice(0, 6)}`;
          const state = get();
          const sourceNode = state.nodes.find(n => n.id === connection.source);
          
          // Determine content type based on source node
          const isFromStartNode = sourceNode?.data.type === 'start';
          const isFromConditionBranch = connection.sourceHandle === 'true' || connection.sourceHandle === 'false';
          
          let contentType: ArrowData['contentType'];
          if (isFromStartNode) {
            contentType = 'empty';
          } else if (isFromConditionBranch) {
            contentType = 'generic';
          }
          
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
              label: 'New Arrow',
              contentType,
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
                personId: undefined,
                llmApi: undefined,
                apiKeyId: undefined,
                modelName: undefined,
                defaultPrompt: '',
                firstOnlyPrompt: '',
                detectedVariables: [],
                contextCleaningRule: 'uponRequest',
                contextCleaningTurns: undefined,
                iterationCount: 1
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
        
        // Batch operations
        setNodes: (nodes: DiagramNode[]) => {
          set({ nodes });
        },
        
        setArrows: (arrows: Arrow[]) => {
          // Process arrows to set proper content type based on source node
          const nodes = get().nodes;
          const processedArrows = arrows.map(arrow => {
            const sourceNode = nodes.find(n => n.id === arrow.source);
            const isFromStartNode = sourceNode?.data.type === 'start';
            const isFromConditionBranch = arrow.sourceHandle === 'true' || arrow.sourceHandle === 'false';
            
            if (arrow.data) {
              if (isFromStartNode) {
                return {
                  ...arrow,
                  data: {
                    ...arrow.data,
                    contentType: 'empty' as const
                  }
                };
              } else if (isFromConditionBranch) {
                return {
                  ...arrow,
                  data: {
                    ...arrow.data,
                    contentType: 'generic' as const
                  }
                };
              }
            }
            return arrow;
          });
          
          set({ arrows: processedArrows });
        },
        
        clearNodesAndArrows: () => {
          set({ nodes: [], arrows: [] });
        },
      })
    )
  )
);