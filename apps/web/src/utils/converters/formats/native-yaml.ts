/**
 * Native YAML format converter for DomainDiagram
 * Handles conversion between YAML array format and DomainDiagram Record format
 */

import { parse, stringify } from 'yaml';
import type { 
  DomainDiagram, 
  DomainNode, 
  DomainArrow, 
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  ApiKeyID
} from '@/types';

// YAML file format (uses arrays)
interface YamlFileDiagram {
  id?: string;
  name?: string;
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
  apiKeys: DomainApiKey[];
}

// YAML stringify options for consistent output
const YAML_STRINGIFY_OPTIONS = {
  indent: 2,
  lineWidth: 120,
  defaultStringType: 'PLAIN' as const,
  defaultKeyType: 'PLAIN' as const,
  simpleKeys: true,
  sortKeys: false
};

export class NativeYamlConverter {
  /**
   * Serialize DomainDiagram to YAML string (converts Records to arrays)
   */
  static serialize(diagram: DomainDiagram): string {
    const yamlDiagram: YamlFileDiagram = {
      nodes: Object.values(diagram.nodes),
      arrows: Object.values(diagram.arrows),
      handles: Object.values(diagram.handles),
      persons: Object.values(diagram.persons),
      apiKeys: Object.values(diagram.apiKeys)
    };
    
    // Add metadata if present
    if (diagram.metadata) {
      yamlDiagram.id = diagram.metadata.id;
      yamlDiagram.name = diagram.metadata.name;
    }
    
    return stringify(yamlDiagram, YAML_STRINGIFY_OPTIONS);
  }

  /**
   * Deserialize YAML string to DomainDiagram (converts arrays to Records)
   */
  static deserialize(yamlString: string): DomainDiagram {
    const data = parse(yamlString) as YamlFileDiagram;
    
    // Validate basic structure
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid YAML: must be an object');
    }
    
    // Check for required fields
    if (!data.nodes || !Array.isArray(data.nodes)) {
      throw new Error('Invalid YAML: missing or invalid nodes array');
    }
    
    if (!data.arrows || !Array.isArray(data.arrows)) {
      throw new Error('Invalid YAML: missing or invalid arrows array');
    }
    
    // Convert arrays to Records
    const diagram: DomainDiagram = {
      nodes: {},
      arrows: {},
      handles: {},
      persons: {},
      apiKeys: {}
    };
    
    // Convert nodes
    data.nodes.forEach(node => {
      diagram.nodes[node.id as NodeID] = node;
    });
    
    // Convert arrows
    data.arrows.forEach(arrow => {
      diagram.arrows[arrow.id as ArrowID] = arrow;
    });
    
    // Convert handles
    if (data.handles && Array.isArray(data.handles)) {
      data.handles.forEach(handle => {
        diagram.handles[handle.id as HandleID] = handle;
      });
    }
    
    // Convert persons
    if (data.persons && Array.isArray(data.persons)) {
      data.persons.forEach(person => {
        diagram.persons[person.id as PersonID] = person;
      });
    }
    
    // Convert API keys
    if (data.apiKeys && Array.isArray(data.apiKeys)) {
      data.apiKeys.forEach(apiKey => {
        diagram.apiKeys[apiKey.id as ApiKeyID] = apiKey;
      });
    }
    
    // Add metadata if present
    if (data.id || data.name) {
      diagram.metadata = {
        id: data.id,
        name: data.name,
        version: '2.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString()
      };
    }
    
    return diagram;
  }
}

// Export convenience functions
export const toNativeYAML = (diagram: DomainDiagram): string => {
  return NativeYamlConverter.serialize(diagram);
};

export const fromNativeYAML = (yamlString: string): DomainDiagram => {
  return NativeYamlConverter.deserialize(yamlString);
};