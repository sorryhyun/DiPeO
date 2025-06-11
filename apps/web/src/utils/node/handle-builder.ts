// Utility for building node handles from configuration

import { createHandleId, nodeId, type NodeConfigItem, type HandleConfig, type DomainHandle, type NodeID } from '@/types';
import { DataType, HandlePosition } from '@/types/primitives';
import { HANDLE_REGISTRY, getHandleConfig } from '@/config/handleRegistry';

/**
 * Map string position to HandlePosition type
 */
function mapToHandlePosition(position: string): HandlePosition {
  switch (position) {
    case 'top': return 'top';
    case 'right': return 'right';
    case 'bottom': return 'bottom';
    case 'left': return 'left';
    default: return 'left';
  }
}

/**
 * Map string data type to DataType type
 */
function mapToDataType(dataType: string): DataType {
  switch (dataType) {
    case 'string': return 'string';
    case 'number': return 'number';
    case 'boolean': return 'boolean';
    case 'object': return 'object';
    case 'array': return 'array';
    case 'any': return 'any';
    default: return 'any';
  }
}

/**
 * Generate handle objects for a node based on its configuration
 */
export function generateNodeHandles(
  nodeId: string, 
  nodeConfig: NodeConfigItem,
  nodeType?: string
): DomainHandle[] {
  // Use centralized registry if available for this node type
  if (nodeType && HANDLE_REGISTRY[nodeType]) {
    return generateNodeHandlesFromRegistry(nodeId, nodeType);
  }
  
  // Fallback to config-based generation
  const handles: DomainHandle[] = [];
  
  // Generate input handles
  if (nodeConfig.handles.input) {
    nodeConfig.handles.input.forEach((handleConfig) => {
      const handle = createHandleFromConfig(nodeId, handleConfig, 'input');
      handles.push(handle);
    });
  }
  
  // Generate output handles
  if (nodeConfig.handles.output) {
    nodeConfig.handles.output.forEach((handleConfig) => {
      const handle = createHandleFromConfig(nodeId, handleConfig, 'output');
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
): DomainHandle[] {
  const handles: DomainHandle[] = [];
  const config = getHandleConfig(nodeType);
  
  // Generate input handles
  if (config.inputs) {
    config.inputs.forEach((handleDef) => {
      handles.push({
        id: createHandleId(nodeId as NodeID, handleDef.id),
        nodeId: nodeId as NodeID,
        name: handleDef.id,
        direction: 'input',
        dataType: mapToDataType(inferDataType(handleDef.id)),
        position: mapToHandlePosition(handleDef.position),
        label: handleDef.label || handleDef.id,
      });
    });
  }
  
  // Generate output handles
  if (config.outputs) {
    config.outputs.forEach((handleDef) => {
      handles.push({
        id: createHandleId(nodeId as NodeID, handleDef.id),
        nodeId: nodeId as NodeID,
        name: handleDef.id,
        direction: 'output',
        dataType: mapToDataType(inferDataType(handleDef.id)),
        position: mapToHandlePosition(handleDef.position),
        label: handleDef.label || handleDef.id,
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
  direction: 'input' | 'output'
): DomainHandle {
  const handleName = config.id || (direction === 'input' ? 'input' : 'output');
  const handleId = createHandleId(nodeId as NodeID, handleName);
  
  return {
    id: handleId,
    nodeId: nodeId as NodeID,
    name: handleName,
    direction,
    dataType: mapToDataType(inferDataType(handleName)),
    position: mapToHandlePosition(config.position || (direction === 'input' ? 'left' : 'right')),
    label: config.label || handleName,
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
export function getDefaultHandles(nodeId: string, nodeType: string): DomainHandle[] {
  const defaultInputHandle: DomainHandle = {
    id: createHandleId(nodeId as NodeID, 'input'),
    nodeId: nodeId as NodeID,
    name: 'input',
    direction: 'input',
    dataType: 'any',
    position: 'left',
  };
  
  const defaultOutputHandle: DomainHandle = {
    id: createHandleId(nodeId as NodeID, 'output'),
    nodeId: nodeId as NodeID,
    name: 'output',
    direction: 'output',
    dataType: 'any',
    position: 'right',
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
          id: createHandleId(nodeId as NodeID, 'true'),
          nodeId: nodeId as NodeID,
          name: 'true',
          direction: 'output',
          position: 'right',
          label: 'true',
          dataType: 'boolean',
        },
        {
          id: createHandleId(nodeId as NodeID, 'false'),
          nodeId: nodeId as NodeID,
          name: 'false',
          direction: 'output',
          position: 'right',
          label: 'false',
          dataType: 'boolean',
        },
      ];
      
    default:
      // Most nodes have both input and output
      return [defaultInputHandle, defaultOutputHandle];
  }
}