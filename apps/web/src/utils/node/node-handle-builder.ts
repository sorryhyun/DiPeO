// Utility for building node handles from configuration

import type { Handle, NodeConfigItem, HandleConfig } from '@/types';
import { createHandleId } from '../canvas/handle-adapter';
import { HANDLE_REGISTRY, getHandleConfig } from '@/config/handleRegistry';

/**
 * Generate handle objects for a node based on its configuration
 */
export function generateNodeHandles(
  nodeId: string, 
  nodeConfig: NodeConfigItem,
  nodeType?: string
): Handle[] {
  // Use centralized registry if available for this node type
  if (nodeType && HANDLE_REGISTRY[nodeType]) {
    return generateNodeHandlesFromRegistry(nodeId, nodeType);
  }
  
  // Fallback to config-based generation
  const handles: Handle[] = [];
  
  // Generate input handles
  if (nodeConfig.handles.input) {
    nodeConfig.handles.input.forEach((handleConfig) => {
      const handle = createHandleFromConfig(nodeId, handleConfig, 'target');
      handles.push(handle);
    });
  }
  
  // Generate output handles
  if (nodeConfig.handles.output) {
    nodeConfig.handles.output.forEach((handleConfig) => {
      const handle = createHandleFromConfig(nodeId, handleConfig, 'source');
      handles.push(handle);
    });
  }
  
  return handles;
}

/**
 * Generate handles from the centralized registry
 */
export function generateNodeHandlesFromRegistry(
  nodeId: string,
  nodeType: string
): Handle[] {
  const handles: Handle[] = [];
  const config = getHandleConfig(nodeType);
  
  // Generate input handles
  if (config.inputs) {
    config.inputs.forEach((handleDef) => {
      handles.push({
        id: createHandleId(nodeId, handleDef.id),
        kind: 'target',
        name: handleDef.id,
        position: handleDef.position,
        label: handleDef.label || handleDef.id,
        dataType: inferDataType(handleDef.id),
      });
    });
  }
  
  // Generate output handles
  if (config.outputs) {
    config.outputs.forEach((handleDef) => {
      handles.push({
        id: createHandleId(nodeId, handleDef.id),
        kind: 'source',
        name: handleDef.id,
        position: handleDef.position,
        label: handleDef.label || handleDef.id,
        dataType: inferDataType(handleDef.id),
      });
    });
  }
  
  return handles;
}

/**
 * Create a Handle object from HandleConfig
 */
function createHandleFromConfig(
  nodeId: string, 
  config: HandleConfig, 
  kind: 'source' | 'target'
): Handle {
  const handleName = config.id || (kind === 'source' ? 'output' : 'input');
  const handleId = createHandleId(nodeId, handleName);
  
  return {
    id: handleId,
    kind,
    name: handleName,
    position: config.position || (kind === 'source' ? 'right' : 'left'),
    label: config.label || handleName,
    dataType: inferDataType(handleName),
  };
}

/**
 * Infer data type from handle name
 */
function inferDataType(handleName: string): string {
  // Special cases for specific handle names
  if (handleName === 'true' || handleName === 'false') {
    return 'boolean';
  }
  
  if (handleName === 'results' || handleName === 'data') {
    return 'object';
  }
  
  if (handleName === 'output' || handleName === 'input' || handleName === 'default') {
    return 'any';
  }
  
  // Default to 'any' for flexibility
  return 'any';
}

/**
 * Get default handles for a node type when no configuration is provided
 */
export function getDefaultHandles(nodeId: string, nodeType: string): Handle[] {
  const defaultInputHandle: Handle = {
    id: createHandleId(nodeId, 'input'),
    kind: 'target',
    name: 'input',
    position: 'left',
    dataType: 'any',
  };
  
  const defaultOutputHandle: Handle = {
    id: createHandleId(nodeId, 'output'),
    kind: 'source',
    name: 'output',
    position: 'right',
    dataType: 'any',
  };
  
  // Special cases for specific node types
  switch (nodeType) {
    case 'start':
      // Start nodes only have output
      return [defaultOutputHandle];
      
    case 'endpoint':
      // Endpoint nodes only have input
      return [defaultInputHandle];
      
    case 'condition':
      // Condition nodes have special true/false outputs
      return [
        defaultInputHandle,
        {
          id: createHandleId(nodeId, 'true'),
          kind: 'source',
          name: 'true',
          position: 'right',
          label: 'True',
          dataType: 'boolean',
        },
        {
          id: createHandleId(nodeId, 'false'),
          kind: 'source',
          name: 'false',
          position: 'right',
          label: 'False',
          dataType: 'boolean',
        },
      ];
      
    default:
      // Most nodes have both input and output
      return [defaultInputHandle, defaultOutputHandle];
  }
}