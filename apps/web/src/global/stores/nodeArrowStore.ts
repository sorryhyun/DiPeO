import { create } from 'zustand';
import { devtools, subscribeWithSelector, persist } from 'zustand/middleware';
import {
  OnNodesChange, OnConnect,
  applyNodeChanges, Connection
} from '@xyflow/react';
import { nanoid } from 'nanoid';
import {
  ArrowData, DiagramNode, DiagramNodeData,
  getReactFlowType, OnArrowsChange, Arrow, applyArrowChanges, addArrow
} from '@/shared/types';
import { getNodeConfig } from '@/shared/types/nodeConfig';

// Factory function to create default node data based on node config
function createDefaultNodeData(type: string, nodeId: string): DiagramNodeData {
  const config = getNodeConfig(type);
  
  if (!config) {
    // Fallback for unknown types
    return {
      id: nodeId,
      type: 'start' as const,
      label: 'Unknown'
    };
  }
  
  // Base properties common to all nodes
  const baseData: Record<string, unknown> = {
    id: nodeId,
    type,
    label: config.label
  };
  
  // Add type-specific properties based on config and defaults
  switch (type) {
    case 'start':
      baseData.description = '';
      break;
      
    case 'person_job':
      baseData.personId = undefined;
      baseData.llmApi = undefined;
      baseData.apiKeyId = undefined;
      baseData.modelName = undefined;
      baseData.defaultPrompt = '';
      baseData.firstOnlyPrompt = '';
      baseData.detectedVariables = [];
      baseData.contextCleaningRule = 'uponRequest';
      baseData.contextCleaningTurns = undefined;
      baseData.iterationCount = 1;
      break;
      
    case 'job':
      baseData.subType = 'code';
      baseData.sourceDetails = '';
      baseData.description = '';
      break;
      
    case 'condition':
      baseData.conditionType = 'expression';
      baseData.expression = '';
      break;
      
    case 'db':
      baseData.subType = 'fixed_prompt';
      baseData.sourceDetails = 'Enter your fixed prompt or content here';
      baseData.description = '';
      break;
      
    case 'endpoint':
      baseData.description = '';
      baseData.saveToFile = false;
      baseData.filePath = '';
      baseData.fileFormat = 'json';
      break;
      
    case 'person_batch_job':
      baseData.personId = undefined;
      baseData.batchPrompt = '';
      baseData.batchSize = 10;
      baseData.parallelProcessing = false;
      baseData.aggregationMethod = 'concatenate';
      baseData.customAggregationPrompt = '';
      baseData.iterationCount = 1;
      break;
  }
  
  return baseData as DiagramNodeData;
}

export interface NodeArrowState {
  nodes: DiagramNode[];
  arrows: Arrow[];

  onNodesChange: OnNodesChange;
  onArrowsChange: OnArrowsChange;
  onConnect: OnConnect;
  addNode: (type: string, position: { x: number; y: number }) => void;
  updateNodeData: (nodeId: string, data: Partial<DiagramNodeData>) => void;
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
    persist(
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
            const arrowId = `arrow-${nanoid().slice(0, 6).replace(/-/g, '_')}`;
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
                label: isFromConditionBranch ? connection.sourceHandle! : 'New Arrow',
                contentType,
                // Set branch property for condition node arrows
                ...(isFromConditionBranch && {
                  branch: connection.sourceHandle as 'true' | 'false'
                })
              }
            };
            set({ arrows: addArrow(newArrow, get().arrows) });
          },

          addNode: (type: string, position: { x: number; y: number }) => {
            const reactFlowType = getReactFlowType(type);
            const nodeId = `${reactFlowType}-${nanoid().slice(0, 6).replace(/-/g, '_')}`;
            
            const nodeData = createDefaultNodeData(type, nodeId);

            const newNode: DiagramNode = {
              id: nodeId,
              type : reactFlowType,
              position,
              data: nodeData,
            };

            set({ nodes: [...get().nodes, newNode] });
          },

          updateNodeData: (nodeId: string, data: Partial<DiagramNodeData>) => {
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
                      contentType: 'generic' as const,
                      // Set branch property for condition node arrows
                      branch: arrow.sourceHandle as 'true' | 'false'
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
      ),
      {
        name: 'dipeo-node-arrow-store',
        // Only persist nodes and arrows, not functions
        partialize: (state) => ({ 
          nodes: state.nodes, 
          arrows: state.arrows 
        }),
      }
    )
  )
);