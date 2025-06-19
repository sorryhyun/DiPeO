/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */

import { UnifiedStore } from '@/core/store/unifiedStore.types';
import { HandleDirection, DataType } from '@dipeo/domain-models';
import { UNIFIED_NODE_CONFIGS } from '@/core/config';
import { storeMapsToArrays } from '@/graphql/types';

// The serialized diagram should match the GraphQL schema format
export interface SerializedDiagram {
  nodes: any[];
  arrows: any[];
  persons: any[];
  handles: any[];
  apiKeys: any[];
  metadata: {
    name?: string | null;
    description?: string | null;
    author?: string | null;
    tags?: string[] | null;
    created: string;
    modified: string;
    version: string;
    id?: string | null;
  };
}


/**
 * Cleans node data by removing React Flow UI-specific properties
 */
function cleanNodeData(node: any): any {
  const { data, ...nodeProps } = node;
  
  // Remove UI-specific properties from data (but keep flipped for visual layout)
  const { _handles: _, inputs: _inputs, outputs: _outputs, type: _type, ...cleanData } = data as any;
  
  return {
    ...nodeProps,
    data: cleanData
  };
}

/**
 * Generates handles for a node based on its type configuration
 */
function generateHandlesForNode(node: any): any[] {
  const handles: any[] = [];
  const nodeType = node.type as string;
  const config = UNIFIED_NODE_CONFIGS[nodeType as keyof typeof UNIFIED_NODE_CONFIGS];
  
  if (!config?.handles) {
    return handles;
  }
  
  // Generate input handles
  if (config.handles.input) {
    config.handles.input.forEach((handleConfig: any) => {
      const handleId = `${node.id}:${handleConfig.id}`;
      handles.push({
        id: handleId,
        nodeId: node.id,
        label: handleConfig.label || handleConfig.id,
        direction: HandleDirection.INPUT,
        dataType: DataType.ANY,
        position: handleConfig.position || 'left'
      });
    });
  }
  
  // Generate output handles
  if (config.handles.output) {
    config.handles.output.forEach((handleConfig: any) => {
      const handleId = `${node.id}:${handleConfig.id}`;
      handles.push({
        id: handleId,
        nodeId: node.id,
        label: handleConfig.label || handleConfig.id,
        direction: HandleDirection.OUTPUT,
        dataType: DataType.ANY,
        position: handleConfig.position || 'right'
      });
    });
  }
  
  return handles;
}

/**
 * Serializes the current diagram state from the store
 */
export function serializeDiagramState(store: UnifiedStore): SerializedDiagram {
  // Get current timestamp
  const now = new Date();
  
  // Create metadata
  const metadata = {
    name: 'Untitled Diagram',
    description: null,
    author: null,
    tags: null,
    created: now.toISOString(),
    modified: now.toISOString(),
    version: '1.0.0',
    id: null
  };
  
  // Convert store Maps to arrays using GraphQL utility
  const diagramArrays = storeMapsToArrays({
    nodes: store.nodes,
    handles: store.handles,
    arrows: store.arrows,
    persons: store.persons,
    apiKeys: store.apiKeys
  });
  
  // Clean node data and generate handles
  const cleanNodes = diagramArrays.nodes?.map(node => cleanNodeData(node)) || [];
  const generatedHandles: any[] = [];
  
  // Generate handles for all nodes
  cleanNodes.forEach(node => {
    const nodeHandles = generateHandlesForNode(node);
    generatedHandles.push(...nodeHandles);
  });
  
  // Use generated handles if store handles are empty
  const handles = diagramArrays.handles && diagramArrays.handles.length > 0 
    ? diagramArrays.handles 
    : generatedHandles;
  
  // Return the serialized diagram
  return {
    nodes: cleanNodes,
    arrows: diagramArrays.arrows || [],
    persons: diagramArrays.persons || [],
    handles,
    apiKeys: diagramArrays.apiKeys || [],
    metadata
  };
}

