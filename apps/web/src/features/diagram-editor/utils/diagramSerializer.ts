/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */

import { HandleDirection, HandleLabel, DataType, createHandleId, NodeID } from '@dipeo/domain-models';
import { DomainNode, DomainArrow, DomainPerson, DomainHandle } from '@/core/types';
import { getNodeConfig } from '@/features/diagram-editor/config/nodes';
import { diagramMapsToArrays } from '@/lib/graphql/types';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { ConversionService } from '@/core/services/ConversionService';

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
      // Ensure max_iteration is a number
      nodeData.max_iteration = typeof nodeData.max_iteration === 'number' 
        ? nodeData.max_iteration 
        : (Number(nodeData.max_iteration) || 1);
      // Convert tools from comma-separated string to array format
      if (typeof nodeData.tools === 'string') {
        nodeData.tools = nodeData.tools ? ConversionService.stringToToolsArray(nodeData.tools) : null;
      }
      break;
    case 'person_batch_job':
      nodeData.first_only_prompt = nodeData.first_only_prompt || '';
      // Ensure max_iteration is a number
      nodeData.max_iteration = typeof nodeData.max_iteration === 'number' 
        ? nodeData.max_iteration 
        : (Number(nodeData.max_iteration) || 1);
      // Convert tools from comma-separated string to array format
      if (typeof nodeData.tools === 'string') {
        nodeData.tools = nodeData.tools ? ConversionService.stringToToolsArray(nodeData.tools) : null;
      }
      break;
    case 'endpoint':
      nodeData.save_to_file = nodeData.save_to_file ?? false;
      break;
    case 'db':
      nodeData.sub_type = nodeData.sub_type || 'fixed_prompt';
      nodeData.operation = nodeData.operation || 'read';
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
  const config = getNodeConfig(nodeType);
  
  if (!config?.handles) {
    return handles;
  }
  
  // Generate input handles
  if (config.handles.input) {
    config.handles.input.forEach((handleConfig: { id: string; label?: string; position?: string }) => {
      const handleLabel = handleConfig.id as HandleLabel;
      const handleId = ConversionService.createHandleId(ConversionService.toNodeId(node.id), handleLabel, HandleDirection.INPUT);
      handles.push({
        id: handleId,
        node_id: node.id,
        label: handleLabel,
        direction: HandleDirection.INPUT,
        data_type: DataType.ANY,
        position: handleConfig.position || 'left'
      });
    });
  }
  
  // Generate output handles
  if (config.handles.output) {
    config.handles.output.forEach((handleConfig: { id: string; label?: string; position?: string }) => {
      const handleLabel = handleConfig.id as HandleLabel;
      const handleId = ConversionService.createHandleId(ConversionService.toNodeId(node.id), handleLabel, HandleDirection.OUTPUT);
      handles.push({
        id: handleId,
        node_id: node.id,
        label: handleLabel,
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
  
  // Convert persons to ensure they have required fields
  const personsWithRequiredFields = new Map(state.persons);
  personsWithRequiredFields.forEach((person, id) => {
    if (person.llm_config && !person.llm_config.api_key_id) {
      // Provide a default api_key_id if missing
      personsWithRequiredFields.set(id, {
        ...person,
        llm_config: {
          ...person.llm_config,
          api_key_id: 'default' as any // This should be a valid ApiKeyID in your system
        }
      });
    }
  });
  
  // Return the Maps with converted persons
  return {
    nodes: state.nodes,
    handles: state.handles,
    arrows: state.arrows,
    persons: personsWithRequiredFields as any
  };
}

/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */
export function serializeDiagram(): SerializedDiagram {
  // Get current timestamp
  const now = new Date();
  
  // Get diagram metadata from store
  const state = useUnifiedStore.getState();
  
  // Create metadata
  const metadata = {
    name: state.diagramName || 'Untitled Diagram',
    description: state.diagramDescription || null,
    author: null,
    tags: null,
    created: now.toISOString(),
    modified: now.toISOString(),
    version: '1.0.0',
    id: state.diagramId || null
  };
  
  // Get store state with properly typed Maps
  const storeMaps = getStoreStateWithMaps();
  const diagramArrays = diagramMapsToArrays(storeMaps);

  // Clean node data
  const cleanNodes = diagramArrays.nodes?.map(node => cleanNodeData(node)) || [];
  
  // Get existing handles from store
  const existingHandles = diagramArrays.handles || [];
  
  // Create a map of existing handles by their handle ID
  const existingHandleMap = ConversionService.arrayToMap(existingHandles, handle => handle.id);
  
  // Generate handles only for nodes that are missing required handles
  const generatedHandles: DomainHandle[] = [];
  cleanNodes.forEach(node => {
    const nodeHandles = generateHandlesForNode(node);
    
    
    nodeHandles.forEach(newHandle => {
      // Only add if this specific handle doesn't exist
      if (!existingHandleMap.has(newHandle.id)) {
        generatedHandles.push(newHandle);
        existingHandleMap.set(newHandle.id, newHandle);
      }
    });
  });
  
  // Use the map values to get all unique handles
  const allHandles = Array.from(existingHandleMap.values());
  
  // Filter out orphaned handles (handles for nodes that don't exist)
  const nodeIds = ConversionService.arrayToUniqueSet(cleanNodes, node => node.id);
  const validHandles = allHandles.filter(handle => {
    if (!nodeIds.has(handle.node_id)) {
      console.warn(`Removing orphaned handle ${handle.id} for non-existent node ${handle.node_id}`);
      return false;
    }
    return true;
  });
  
  // Create a set of valid handle IDs for arrow validation (use allHandles first to validate arrows)
  const allHandleIds = ConversionService.arrayToUniqueSet(allHandles, handle => handle.id);
  
  
  // Filter out arrows that reference invalid handles
  // First check against all handles, then ensure the handles belong to valid nodes
  const validArrows = (diagramArrays.arrows || []).filter(arrow => {
    const sourceValid = allHandleIds.has(arrow.source);
    const targetValid = allHandleIds.has(arrow.target);
    
    if (!sourceValid || !targetValid) {
      console.warn(`Removing arrow ${arrow.id} with invalid handle references: ${arrow.source} -> ${arrow.target}`);
      return false;
    }
    
    // Also check if the handles belong to existing nodes
    const sourceHandle = existingHandleMap.get(arrow.source);
    const targetHandle = existingHandleMap.get(arrow.target);
    
    if (sourceHandle && !nodeIds.has(sourceHandle.node_id)) {
      console.warn(`Removing arrow ${arrow.id} - source handle belongs to non-existent node`);
      return false;
    }
    
    if (targetHandle && !nodeIds.has(targetHandle.node_id)) {
      console.warn(`Removing arrow ${arrow.id} - target handle belongs to non-existent node`);
      return false;
    }
    
    return true;
  });
  
  // Clean persons data by removing masked_api_key
  const cleanPersons = (diagramArrays.persons || []).map(person => {
    // Remove masked_api_key as it's a runtime display-only field
    const { masked_api_key: _masked_api_key, ...cleanPerson } = person as any;
    return cleanPerson as DomainPerson;
  });

  // Return the serialized diagram
  return {
    nodes: cleanNodes,
    arrows: validArrows,
    persons: cleanPersons,
    handles: validHandles,
    metadata
  };
}

