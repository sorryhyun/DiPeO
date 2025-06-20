/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */

import { HandleDirection, DataType } from '@dipeo/domain-models';
import { UNIFIED_NODE_CONFIGS } from '@/core/config';
import { storeMapsToArrays } from '@/graphql/types';
import { useUnifiedStore } from '@/core/store/unifiedStore';

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
  
  // Ensure required fields are present for validation
  const nodeData = {
    ...cleanData
  };
  
  // Add default label if missing
  if (!nodeData.label) {
    nodeData.label = nodeProps.type || 'Node';
  }
  
  // Add node-type specific required fields with defaults
  switch (nodeProps.type) {
    case 'start':
      nodeData.customData = nodeData.customData || {};
      nodeData.outputDataStructure = nodeData.outputDataStructure || {};
      break;
    case 'condition':
      nodeData.conditionType = nodeData.conditionType || 'simple';
      nodeData.detect_max_iterations = nodeData.detect_max_iterations ?? false;
      break;
    case 'person_job':
      nodeData.firstOnlyPrompt = nodeData.firstOnlyPrompt || '';
      nodeData.maxIterations = nodeData.maxIterations || 1;
      break;
    case 'endpoint':
      nodeData.saveToFile = nodeData.saveToFile ?? false;
      break;
    case 'db':
      nodeData.subType = nodeData.subType || 'fixed_prompt';
      nodeData.operation = nodeData.operation || 'read';
      break;
    case 'job':
      nodeData.codeType = nodeData.codeType || 'python';
      nodeData.code = nodeData.code || '';
      break;
    case 'user_response':
      nodeData.prompt = nodeData.prompt || '';
      nodeData.timeout = nodeData.timeout || 60;
      break;
    case 'notion':
      nodeData.operation = nodeData.operation || 'get_page';
      break;
  }
  
  return {
    ...nodeProps,
    data: nodeData
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
 * Gets the current store state and returns properly typed Maps
 */
function getStoreStateWithMaps() {
  const state = useUnifiedStore.getState();
  
  // Direct access to store properties should give us Maps
  // But in case they're serialized, we'll ensure they're Maps
  const ensureMap = (value: any): Map<any, any> => {
    if (value instanceof Map) {
      return value;
    }
    // Handle devtools serialized format
    if (value && typeof value === 'object' && value._type === 'Map' && Array.isArray(value._value)) {
      return new Map(value._value);
    }
    // If it's a plain object, try to convert it
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return new Map(Object.entries(value));
    }
    return new Map();
  };
  
  return {
    nodes: ensureMap(state.nodes),
    handles: ensureMap(state.handles),
    arrows: ensureMap(state.arrows),
    persons: ensureMap(state.persons),
    apiKeys: ensureMap(state.apiKeys)
  };
}

/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */
export function serializeDiagram(): SerializedDiagram {
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
  
  // Get store state with properly typed Maps
  const storeMaps = getStoreStateWithMaps();
  
  console.log('[serializeDiagramStateFromStore] storeMaps:', storeMaps);
  console.log('[serializeDiagramStateFromStore] storeMaps.nodes instanceof Map:', storeMaps.nodes instanceof Map);
  
  // Convert store Maps to arrays using GraphQL utility
  const diagramArrays = storeMapsToArrays(storeMaps);
  
  console.log('[serializeDiagramStateFromStore] diagramArrays:', diagramArrays);
  console.log('[serializeDiagramStateFromStore] diagramArrays.nodes is array:', Array.isArray(diagramArrays.nodes));
  
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

