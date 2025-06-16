/**
 * Serializes the current diagram state from the unified store
 * into a format that can be saved to the backend
 */

import { UnifiedStore } from '@/stores/unifiedStore.types';
import { 
  DomainNode, 
  DomainArrow, 
  DomainPerson, 
  DomainHandle, 
  DomainApiKey
} from '@/types';

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
  
  // Serialize the state
  return {
    nodes: mapToRecord(store.nodes),
    arrows: mapToRecord(store.arrows),
    persons: mapToRecord(store.persons),
    handles: mapToRecord(store.handles),
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