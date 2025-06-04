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
} from '@/common/types';
import { getNodeConfig } from '@/common/types/nodeConfig';

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
              // For condition nodes, inherit content type from input arrows
              const inputArrows = state.arrows.filter(arrow => arrow.target === connection.source);
              
              if (inputArrows.length > 0) {
                // Use the first input arrow's properties (TODO: handle multiple inputs in edge cases)
                const primaryInputArrow = inputArrows[0];
                if (primaryInputArrow?.data) {
                  contentType = primaryInputArrow.data.contentType || 'generic';
                } else {
                  contentType = 'generic';
                }
              } else {
                // No input arrows yet, default to generic
                contentType = 'generic';
              }
            } else {
              // Default content type for regular arrows
              contentType = 'raw_text';
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
                template: '',
                label: isFromConditionBranch ? connection.sourceHandle! : 'New Arrow',
                contentType,
                // Set branch property for condition node arrows
                ...(isFromConditionBranch && {
                  branch: connection.sourceHandle as 'true' | 'false',
                  inheritedContentType: true
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
            const state = get();
            const updatedArrows = state.arrows.map(arrow =>
              arrow.id === arrowId ? { 
                ...arrow, 
                data: { ...arrow.data, ...data } as ArrowData 
              } : arrow
            );
            
            // After updating an arrow, check if it affects condition node outputs
            const updatedArrow = updatedArrows.find(a => a.id === arrowId);
            if (updatedArrow) {
              // Find all arrows that originate from the target node of the updated arrow
              const targetNode = state.nodes.find(n => n.id === updatedArrow.target);
              if (targetNode?.data.type === 'condition') {
                // Update all arrows originating from this condition node
                const finalArrows = updatedArrows.map(arrow => {
                  if (arrow.source === targetNode.id && arrow.data?.inheritedContentType) {
                    return {
                      ...arrow,
                      data: {
                        ...arrow.data,
                        contentType: updatedArrow.data?.contentType || 'generic'
                      } as ArrowData
                    };
                  }
                  return arrow;
                });
                set({ arrows: finalArrows });
                return;
              }
            }
            
            set({ arrows: updatedArrows });
          },

          deleteArrow: (arrowId: string) => {
            const state = get();
            const arrowToDelete = state.arrows.find(a => a.id === arrowId);
            const remainingArrows = state.arrows.filter(arrow => arrow.id !== arrowId);
            
            // If deleting an arrow that goes into a condition node, update its output arrows
            if (arrowToDelete) {
              const targetNode = state.nodes.find(n => n.id === arrowToDelete.target);
              if (targetNode?.data.type === 'condition') {
                // Find remaining input arrows to the condition node
                const remainingInputArrows = remainingArrows.filter(a => a.target === targetNode.id);
                
                // Update all output arrows from the condition node
                const finalArrows = remainingArrows.map(arrow => {
                  if (arrow.source === targetNode.id && arrow.data?.inheritedContentType) {
                    if (remainingInputArrows.length > 0) {
                      const primaryInputArrow = remainingInputArrows[0];
                      if (primaryInputArrow?.data) {
                        return {
                          ...arrow,
                          data: {
                            ...arrow.data,
                            contentType: primaryInputArrow.data.contentType || 'generic'
                          } as ArrowData
                        };
                      }
                    }
                    // No input arrows or no data, reset to generic
                    return {
                      ...arrow,
                      data: {
                        ...arrow.data,
                        contentType: 'generic' as const
                      } as ArrowData
                    };
                  }
                  return arrow;
                });
                set({ arrows: finalArrows });
                return;
              }
            }
            
            set({ arrows: remainingArrows });
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
                  // For condition nodes, inherit content type from input arrows
                  const inputArrows = arrows.filter(a => a.target === arrow.source);
                  let contentType: ArrowData['contentType'] = 'generic';
                  
                  if (inputArrows.length > 0) {
                    const primaryInputArrow = inputArrows[0];
                    if (primaryInputArrow?.data) {
                      contentType = primaryInputArrow.data.contentType || 'generic';
                    }
                  }
                  
                  return {
                    ...arrow,
                    data: {
                      ...arrow.data,
                      contentType,
                      // Set branch property for condition node arrows
                      branch: arrow.sourceHandle as 'true' | 'false',
                      inheritedContentType: true
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