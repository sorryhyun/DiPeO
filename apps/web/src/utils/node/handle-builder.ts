// Utility for building node handles from configuration

import { createHandleId, nodeId, type NodeConfigItem, type HandleConfig, type DomainHandle, type NodeID } from '@/types';
import { DataType, HandlePosition } from '@/types/primitives';
import { HANDLE_REGISTRY, getHandleConfig } from '@/config/handleRegistry';
import { createLookupTable, createHandlerTable } from '@/utils/dispatchTable';

// Create lookup tables for position and data type mappings
const positionLookup = createLookupTable<string, HandlePosition>({
  'top': 'top',
  'right': 'right',
  'bottom': 'bottom',
  'left': 'left'
});

const dataTypeLookup = createLookupTable<string, DataType>({
  'string': 'string',
  'number': 'number',
  'boolean': 'boolean',
  'object': 'object',
  'array': 'array',
  'any': 'any'
});

/**
 * Map string position to HandlePosition type
 */
function mapToHandlePosition(position: string): HandlePosition {
  return positionLookup(position) || 'left';
}

/**
 * Map string data type to DataType type
 */
function mapToDataType(dataType: string): DataType {
  return dataTypeLookup(dataType) || 'any';
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

// Create handler table for node type default handles
const nodeDefaultHandles = createHandlerTable<string, [NodeID, DomainHandle, DomainHandle], DomainHandle[]>({
  'start': (_nodeId, _defaultInput, defaultOutput) => [defaultOutput],
  'endpoint': (_nodeId, defaultInput) => [defaultInput],
  'condition': (nodeIdTyped, defaultInput) => [
    defaultInput,
    {
      id: createHandleId(nodeIdTyped, 'true'),
      nodeId: nodeIdTyped,
      name: 'true',
      direction: 'output',
      position: 'right',
      label: 'true',
      dataType: 'boolean',
    },
    {
      id: createHandleId(nodeIdTyped, 'false'),
      nodeId: nodeIdTyped,
      name: 'false',
      direction: 'output',
      position: 'right',
      label: 'false',
      dataType: 'boolean',
    },
  ]
}, (_nodeId, defaultInput, defaultOutput) => [defaultInput, defaultOutput]); // Default: both handles

/**
 * Get default handles for a node type when no configuration is provided
 */
export function getDefaultHandles(nodeId: string, nodeType: string): DomainHandle[] {
  const nodeIdTyped = nodeId as NodeID;
  
  const defaultInputHandle: DomainHandle = {
    id: createHandleId(nodeIdTyped, 'input'),
    nodeId: nodeIdTyped,
    name: 'input',
    direction: 'input',
    dataType: 'any',
    position: 'left',
  };
  
  const defaultOutputHandle: DomainHandle = {
    id: createHandleId(nodeIdTyped, 'output'),
    nodeId: nodeIdTyped,
    name: 'output',
    direction: 'output',
    dataType: 'any',
    position: 'right',
  };
  
  return nodeDefaultHandles.executeOrDefault(nodeType, nodeIdTyped, defaultInputHandle, defaultOutputHandle);
}