// Utility for building node handles from configuration

import type { Handle, NodeConfigItem, HandleConfig } from '@/types';
import { createHandleId } from '../canvas/handle-adapter';

/**
 * Generate handle objects for a node based on its configuration
 */
export function generateNodeHandles(
  nodeId: string, 
  nodeConfig: NodeConfigItem
): Handle[] {
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
    nodeId,
    kind,
    name: handleName,
    position: config.position || (kind === 'source' ? 'right' : 'left'),
    label: config.label || handleName,
    dataType: inferDataType(handleName, kind),
    style: {
      ...(config.color && { backgroundColor: config.color }),
      ...(config.offset && {
        top: config.offset.y ? `${50 + config.offset.y}%` : '50%',
        transform: config.offset.y ? 'translateY(-50%)' : undefined,
      }),
    },
  };
}

/**
 * Infer data type from handle name and kind
 */
function inferDataType(handleName: string, kind: 'source' | 'target'): string {
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
    nodeId,
    kind: 'target',
    name: 'input',
    position: 'left',
    dataType: 'any',
  };
  
  const defaultOutputHandle: Handle = {
    id: createHandleId(nodeId, 'output'),
    nodeId,
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
          ...defaultOutputHandle,
          id: createHandleId(nodeId, 'true'),
          name: 'true',
          label: 'True',
          dataType: 'boolean',
        },
        {
          ...defaultOutputHandle,
          id: createHandleId(nodeId, 'false'),
          name: 'false',
          label: 'False',
          dataType: 'boolean',
        },
      ];
      
    default:
      // Most nodes have both input and output
      return [defaultInputHandle, defaultOutputHandle];
  }
}