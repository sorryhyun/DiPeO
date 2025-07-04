/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */

import { HandleDirection, DataType, NodeID, ArrowID, PersonID, HandleID } from '@dipeo/domain-models';
import { DomainNode, DomainArrow, DomainPerson, DomainHandle } from '@/core/types';
import { UNIFIED_NODE_CONFIGS } from '@/core/config';
import { storeMapsToArrays, convertGraphQLPersonToDomain, convertGraphQLDiagramToDomain, diagramToStoreMaps } from '@/graphql/types';
import { useUnifiedStore } from '@/core/store/unifiedStore';

// The serialized diagram should match the GraphQL schema format
export interface SerializedDiagram {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  handles: DomainHandle[];
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
function cleanNodeData(node: DomainNode): DomainNode {
  const { data, ...nodeProps } = node;
  
  // Handle case where data is null or undefined
  if (!data) {
    return {
      ...nodeProps,
      data: {
        label: nodeProps.type || 'Node'
      }
    };
  }
  
  // Remove UI-specific properties from data (but keep flipped for visual layout)
  const { _handles: _, inputs: _inputs, outputs: _outputs, type: _type, ...cleanData } = data as Record<string, unknown>;
  
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
      nodeData.custom_data = nodeData.custom_data || {};
      nodeData.output_data_structure = nodeData.output_data_structure || {};
      break;
    case 'condition':
      nodeData.condition_type = nodeData.condition_type || 'simple';
      break;
    case 'person_job':
      nodeData.first_only_prompt = nodeData.first_only_prompt || '';
      nodeData.max_iteration = nodeData.max_iteration || 1;
      // Convert tools from comma-separated string to array format
      if (typeof nodeData.tools === 'string' && nodeData.tools) {
        const toolNames = nodeData.tools.split(',').map((t: string) => t.trim()).filter((t: string) => t);
        nodeData.tools = toolNames.map((toolName: string) => {
          // Map common tool names to their enum values
          const toolTypeMap: Record<string, string> = {
            'web_search': 'web_search',
            'web_search_preview': 'web_search_preview',
            'image_generation': 'image_generation'
          };
          return {
            type: toolTypeMap[toolName] || toolName,
            enabled: true
          };
        });
      } else if (typeof nodeData.tools === 'string' && !nodeData.tools) {
        // Empty string means no tools
        nodeData.tools = null;
      }
      break;
    case 'endpoint':
      nodeData.save_to_file = nodeData.save_to_file ?? false;
      break;
    case 'db':
      nodeData.sub_type = nodeData.sub_type || 'fixed_prompt';
      nodeData.operation = nodeData.operation || 'read';
      break;
    case 'job':
      nodeData.code_type = nodeData.code_type || 'python';
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
function generateHandlesForNode(node: DomainNode): DomainHandle[] {
  const handles: DomainHandle[] = [];
  const nodeType = node.type as string;
  const config = UNIFIED_NODE_CONFIGS[nodeType as keyof typeof UNIFIED_NODE_CONFIGS];
  
  if (!config?.handles) {
    return handles;
  }
  
  // Generate input handles
  if (config.handles.input) {
    config.handles.input.forEach((handleConfig: { id: string; label?: string; position?: string }) => {
      const handleId = `${node.id}:${handleConfig.id}`;
      handles.push({
        id: handleId as import('@dipeo/domain-models').HandleID,
        node_id: node.id,
        label: handleConfig.label || handleConfig.id,
        direction: HandleDirection.INPUT,
        data_type: DataType.ANY,
        position: handleConfig.position || 'left'
      });
    });
  }
  
  // Generate output handles
  if (config.handles.output) {
    config.handles.output.forEach((handleConfig: { id: string; label?: string; position?: string }) => {
      const handleId = `${node.id}:${handleConfig.id}`;
      handles.push({
        id: handleId as import('@dipeo/domain-models').HandleID,
        node_id: node.id,
        label: handleConfig.label || handleConfig.id,
        direction: HandleDirection.OUTPUT,
        data_type: DataType.ANY,
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
  
  // Convert store arrays to a diagram format
  const graphqlDiagram = {
    nodes: state.nodesArray || [],
    handles: Array.from(state.handles?.values() || []),
    arrows: state.arrowsArray || [],
    persons: state.personsArray || []
  };
  
  // Convert GraphQL diagram to domain format (handles type mismatches)
  const domainDiagram = convertGraphQLDiagramToDomain(graphqlDiagram);
  
  // Convert back to Maps
  return diagramToStoreMaps(domainDiagram);
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
  const diagramArrays = storeMapsToArrays(storeMaps);

  // Clean node data and generate handles
  const cleanNodes = diagramArrays.nodes?.map(node => cleanNodeData(node)) || [];
  const generatedHandles: DomainHandle[] = [];
  
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
    metadata
  };
}

