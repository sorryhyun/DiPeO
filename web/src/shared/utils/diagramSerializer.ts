/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */

import { UnifiedStore } from '@/core/store/unifiedStore.types';
import { DomainApiKey, DomainArrow, DomainHandle, DomainNode, DomainPerson, HandleID } from '@/core/types';
import { HandleDirection, DataType, NodeType } from '@dipeo/domain-models';
import { UNIFIED_NODE_CONFIGS } from '@/core/config';

// Define DiagramMetadata locally to avoid circular dependencies
interface DiagramMetadata {
  name: string;
  description: string;
  author: string;
  tags: string[];
  created: string;
  modified: string;
  version?: string;
  id?: string;
}

export interface SerializedDiagram {
  nodes: Record<string, DomainNode>;
  arrows: Record<string, DomainArrow>;
  persons: Record<string, DomainPerson>;
  handles: Record<string, DomainHandle>;
  apiKeys: Record<string, DomainApiKey>;
  metadata: DiagramMetadata;
}

/**
 * Converts Map to Record for serialization
 */
function mapToRecord<K extends string, V>(map: Map<K, V>): Record<K, V> {
  const record: Record<K, V> = {} as Record<K, V>;
  map.forEach((value, key) => {
    record[key] = value;
  });
  return record;
}

/**
 * Cleans node data by removing React Flow UI-specific properties
 */
function cleanNodeData(node: DomainNode): DomainNode {
  const { data, ...nodeProps } = node;
  
  // Remove UI-specific properties from data (but keep flipped for visual layout)
  const { _handles, inputs, outputs, type, ...cleanData } = data as any;
  
  return {
    ...nodeProps,
    data: cleanData
  };
}

/**
 * Generates handles for a node based on its type configuration
 */
function generateHandlesForNode(node: DomainNode): Record<string, DomainHandle> {
  const handles: Record<string, DomainHandle> = {};
  const config = UNIFIED_NODE_CONFIGS[node.type];
  
  if (!config?.handles) {
    return handles;
  }
  
  // Generate input handles
  if (config.handles.input) {
    config.handles.input.forEach(handleConfig => {
      const handleId = `${node.id}:${handleConfig.id}` as HandleID;
      handles[handleId] = {
        id: handleId,
        nodeId: node.id,
        label: handleConfig.label || handleConfig.id,
        direction: HandleDirection.INPUT,
        dataType: DataType.ANY,
        position: handleConfig.position || 'left'
      };
    });
  }
  
  // Generate output handles
  if (config.handles.output) {
    config.handles.output.forEach(handleConfig => {
      const handleId = `${node.id}:${handleConfig.id}` as HandleID;
      handles[handleId] = {
        id: handleId,
        nodeId: node.id,
        label: handleConfig.label || handleConfig.id,
        direction: HandleDirection.OUTPUT,
        dataType: DataType.ANY,
        position: handleConfig.position || 'right'
      };
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
  
  // Create metadata if it doesn't exist
  const metadata: DiagramMetadata = {
    name: 'Untitled Diagram',
    description: '',
    author: '',
    tags: [],
    created: now.toISOString(),
    modified: now.toISOString(),
    version: '1.0.0'
  };
  
  // Generate handles for all nodes and clean node data
  const allHandles: Record<string, DomainHandle> = {};
  const cleanNodes: Record<string, DomainNode> = {};
  
  store.nodes.forEach((node, nodeId) => {
    // Generate handles for this node
    const nodeHandles = generateHandlesForNode(node);
    Object.assign(allHandles, nodeHandles);
    
    // Clean the node data
    cleanNodes[nodeId] = cleanNodeData(node);
  });
  
  // Serialize the state
  return {
    nodes: cleanNodes,
    arrows: mapToRecord(store.arrows),
    persons: mapToRecord(store.persons),
    handles: allHandles, // Use generated handles instead of store.handles
    apiKeys: mapToRecord(store.apiKeys),
    metadata
  };
}

/**
 * Converts the serialized diagram to YAML string
 */
export function serializeToYaml(diagram: SerializedDiagram): string {
  // For now, we'll use JSON and let the backend handle conversion
  // In the future, we could use a YAML library here
  return JSON.stringify(diagram, null, 2);
}

/**
 * Creates a File object from the serialized diagram
 */
export function createDiagramFile(
  diagram: SerializedDiagram, 
  filename: string = 'diagram.json'
): File {
  const content = JSON.stringify(diagram, null, 2);
  const blob = new Blob([content], { type: 'application/json' });
  return new File([blob], filename, { type: 'application/json' });
}