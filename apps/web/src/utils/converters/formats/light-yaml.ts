/**
 * Light YAML format converter for DiPeO diagrams
 * 
 * Provides a reduced, cleaner YAML format that's more readable than JSON
 * while maintaining all necessary information for diagram reconstruction
 * Works directly with DomainDiagram types
 */

import { stringify, parse } from 'yaml';
import {
  DomainDiagram, DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  NodeID, ArrowID, PersonID, ApiKeyID, HandleID,
  NodeKind, LLMService, DataType,
  generateNodeId, generateShortId, arrowId, personId, apiKeyId, handleId,
  parseHandleId, createHandleId
} from '@/types';
import { YAML_VERSION, YAML_STRINGIFY_OPTIONS } from '../constants';
import { DomainFormatConverter } from '../core/types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';

// Reduced YAML format types
export interface ReducedYamlNode {
  label: string;
  type: string;
  position: { x: number; y: number };
  // Node-specific data fields
  [key: string]: any;
}

export interface ReducedYamlArrow {
  from: string;      // nodeLabel:handleName
  to: string;        // nodeLabel:handleName
  label?: string;
  [key: string]: any;
}

export interface ReducedYamlPerson {
  model: string;
  service?: string;
  apiKey?: string;   // API key label
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

export interface ReducedYamlApiKey {
  service: string;
}

export interface ReducedYamlHandle {
  node: string;      // Node label
  name: string;      // Handle name
  direction: 'input' | 'output';
  dataType: string;
  position: 'left' | 'right' | 'top' | 'bottom';
  maxConnections?: number;
}

export interface ReducedYamlFormat {
  version: string;
  name?: string;
  description?: string;
  nodes: Record<string, ReducedYamlNode>;
  connections: ReducedYamlArrow[];
  persons?: Record<string, ReducedYamlPerson>;
  apiKeys?: Record<string, ReducedYamlApiKey>;
  handles?: ReducedYamlHandle[];
}

export class LightDomainConverter implements DomainFormatConverter {
  readonly formatName = 'light';
  readonly fileExtension = '.yaml';

  // ID to label mappings
  private nodeIdToLabel = new Map<NodeID, string>();
  private handleIdToLabel = new Map<HandleID, string>();
  private personIdToLabel = new Map<PersonID, string>();
  private apiKeyIdToLabel = new Map<ApiKeyID, string>();
  
  // Label to ID mappings (for deserialization)
  private labelToNodeId = new Map<string, NodeID>();
  private labelToHandleId = new Map<string, HandleID>();
  private labelToPersonId = new Map<string, PersonID>();
  private labelToApiKeyId = new Map<string, ApiKeyID>();

  serialize(diagram: DomainDiagram): string {
    const yamlData = this.toReducedYamlFormat(diagram);
    return stringify(yamlData, YAML_STRINGIFY_OPTIONS);
  }

  deserialize(yamlString: string): DomainDiagram {
    const data = parse(yamlString) as ReducedYamlFormat;
    return this.fromReducedYamlFormat(data);
  }

  private reset(): void {
    this.nodeIdToLabel.clear();
    this.handleIdToLabel.clear();
    this.personIdToLabel.clear();
    this.apiKeyIdToLabel.clear();
    this.labelToNodeId.clear();
    this.labelToHandleId.clear();
    this.labelToPersonId.clear();
    this.labelToApiKeyId.clear();
  }

  /**
   * Convert DomainDiagram to reduced YAML format
   */
  private toReducedYamlFormat(diagram: DomainDiagram): ReducedYamlFormat {
    this.reset();
    
    const nodes: Record<string, ReducedYamlNode> = {};
    const connections: ReducedYamlArrow[] = [];
    const persons: Record<string, ReducedYamlPerson> = {};
    const apiKeys: Record<string, ReducedYamlApiKey> = {};
    const handles: ReducedYamlHandle[] = [];
    
    // Convert API keys first (build ID to label mapping)
    Object.entries(diagram.apiKeys).forEach(([id, key]) => {
      const label = key.label || `API_KEY_${id}`;
      this.apiKeyIdToLabel.set(id as ApiKeyID, label);
      apiKeys[label] = {
        service: key.service
      };
    });
    
    // Convert persons (build ID to label mapping)
    Object.entries(diagram.persons).forEach(([id, person]) => {
      const label = person.label || `PERSON_${id}`;
      this.personIdToLabel.set(id as PersonID, label);
      
      const reducedPerson: ReducedYamlPerson = {
        model: person.model
      };
      
      // Only add non-default values
      if (person.service !== 'openai') reducedPerson.service = person.service;
      if (person.apiKeyId) {
        const apiKeyLabel = this.apiKeyIdToLabel.get(person.apiKeyId);
        if (apiKeyLabel) reducedPerson.apiKey = apiKeyLabel;
      }
      if (person.systemPrompt) reducedPerson.systemPrompt = person.systemPrompt;
      if (person.temperature !== undefined && person.temperature !== 0.2) {
        reducedPerson.temperature = person.temperature;
      }
      if (person.maxTokens) reducedPerson.maxTokens = person.maxTokens;
      if (person.topP !== undefined && person.topP !== 1) reducedPerson.topP = person.topP;
      if (person.frequencyPenalty) reducedPerson.frequencyPenalty = person.frequencyPenalty;
      if (person.presencePenalty) reducedPerson.presencePenalty = person.presencePenalty;
      
      persons[label] = reducedPerson;
    });
    
    // Convert handles (build ID to label mapping)
    Object.entries(diagram.handles).forEach(([id, handle]) => {
      const label = handle.label || `HANDLE_${id}`;
      this.handleIdToLabel.set(id as HandleID, label);
    });
    
    // Convert nodes (build ID to label mapping)
    Object.entries(diagram.nodes).forEach(([id, node]) => {
      const label = String(node.data.label || `NODE_${id}`);
      this.nodeIdToLabel.set(id as NodeID, label);
      
      const reducedNode: ReducedYamlNode = {
        label,
        type: node.type,
        position: {
          x: Math.round(node.position.x),
          y: Math.round(node.position.y)
        }
      };
      
      // Add data fields directly to node (except internal fields)
      Object.entries(node.data).forEach(([key, value]) => {
        // Skip internal/computed fields
        if (key === 'id' || key === 'handles' || key === 'type' || key === 'label') return;
        
        // Replace personId with personLabel
        if (key === 'personId' && value) {
          const personLabel = this.personIdToLabel.get(value as PersonID);
          if (personLabel) {
            reducedNode.person = personLabel;
            return;
          }
        }
        
        // Add other fields directly
        reducedNode[key] = value;
      });
      
      nodes[label] = reducedNode;
    });
    
    // Convert arrows
    Object.entries(diagram.arrows).forEach(([id, arrow]) => {
      // Parse handle IDs to get node IDs and handle labels
      const { nodeId: sourceNodeId, handleLabel: sourceHandleLabel } = parseHandleId(arrow.source);
      const { nodeId: targetNodeId, handleLabel: targetHandleLabel } = parseHandleId(arrow.target);
      
      const sourceNodeLabel = this.nodeIdToLabel.get(sourceNodeId);
      const targetNodeLabel = this.nodeIdToLabel.get(targetNodeId);
      
      if (!sourceNodeLabel || !targetNodeLabel || !sourceHandleLabel || !targetHandleLabel) {
        console.warn(`Skipping arrow ${id} due to missing node or handle labels`);
        return;
      }
      
      const reducedArrow: ReducedYamlArrow = {
        from: `${sourceNodeLabel}:${sourceHandleLabel}`,
        to: `${targetNodeLabel}:${targetHandleLabel}`
      };
      
      // Add data fields if present
      if (arrow.data && Object.keys(arrow.data).length > 0) {
        Object.entries(arrow.data).forEach(([key, value]) => {
          reducedArrow[key] = value;
        });
      }
      
      connections.push(reducedArrow);
    });
    
    // Convert custom handles only
    Object.entries(diagram.handles).forEach(([id, handle]) => {
      const nodeLabel = this.nodeIdToLabel.get(handle.nodeId);
      if (!nodeLabel) return;
      
      // Skip default handles that would be auto-generated
      const node = diagram.nodes[handle.nodeId];
      if (node) {
        const defaultHandles = generateNodeHandlesFromRegistry(node.type as NodeKind, handle.nodeId);
        const isDefault = defaultHandles.some(dh => 
          dh.label === handle.label &&
          dh.direction === handle.direction &&
          dh.dataType === handle.dataType &&
          dh.position === handle.position
        );
        if (isDefault) return;
      }
      
      handles.push({
        node: nodeLabel,
        name: handle.label,
        direction: handle.direction,
        dataType: handle.dataType,
        position: handle.position || 'bottom',
        maxConnections: handle.maxConnections
      });
    });
    
    // Build final format
    const result: ReducedYamlFormat = {
      version: YAML_VERSION,
      nodes,
      connections
    };
    
    // Only add optional fields if they have content
    if (diagram.metadata?.name) result.name = diagram.metadata.name;
    if (diagram.metadata?.description) result.description = diagram.metadata.description;
    if (Object.keys(persons).length > 0) result.persons = persons;
    if (Object.keys(apiKeys).length > 0) result.apiKeys = apiKeys;
    if (handles.length > 0) result.handles = handles;
    
    return result;
  }

  /**
   * Convert from reduced YAML format to DomainDiagram
   */
  private fromReducedYamlFormat(data: ReducedYamlFormat): DomainDiagram {
    this.reset();
    
    const diagram: DomainDiagram = {
      nodes: {},
      arrows: {},
      handles: {},
      persons: {},
      apiKeys: {}
    };
    
    // Import API keys first
    if (data.apiKeys) {
      Object.entries(data.apiKeys).forEach(([label, apiKey]) => {
        const id = apiKeyId(generateShortId());
        this.labelToApiKeyId.set(label, id);
        diagram.apiKeys[id] = {
          id,
          label,
          service: apiKey.service as LLMService
        };
      });
    }
    
    // Import persons
    if (data.persons) {
      Object.entries(data.persons).forEach(([label, person]) => {
        const id = personId(generateShortId());
        this.labelToPersonId.set(label, id);
        
        let apiKeyId: ApiKeyID | undefined;
        if (person.apiKey) {
          apiKeyId = this.labelToApiKeyId.get(person.apiKey);
        }
        
        diagram.persons[id] = {
          id,
          label,
          model: person.model,
          service: (person.service || 'openai') as LLMService,
          apiKeyId,
          systemPrompt: person.systemPrompt || '',
          temperature: person.temperature ?? 0.2,
          maxTokens: person.maxTokens,
          topP: person.topP ?? 1,
          frequencyPenalty: person.frequencyPenalty ?? 0,
          presencePenalty: person.presencePenalty ?? 0
        };
      });
    }
    
    // Import nodes
    Object.entries(data.nodes).forEach(([label, node]) => {
      const nodeId = generateNodeId();
      this.labelToNodeId.set(label, nodeId);
      
      // Extract node properties
      const { type, position, label: nodeLabel, ...restData } = node;
      
      const nodeData: any = {
        label,
        ...restData
      };
      
      // Convert person reference
      if (nodeData.person) {
        const personId = this.labelToPersonId.get(nodeData.person);
        if (personId) {
          nodeData.personId = personId;
          delete nodeData.person;
        }
      }
      
      diagram.nodes[nodeId] = {
        id: nodeId,
        type: type as NodeKind,
        position,
        data: nodeData
      };
    });
    
    // Generate default handles for nodes
    Object.values(diagram.nodes).forEach(node => {
      const handles = generateNodeHandlesFromRegistry(node.type as NodeKind, node.id);
      handles.forEach(handle => {
        this.labelToHandleId.set(handle.label, handle.id);
        diagram.handles[handle.id] = handle;
      });
    });
    
    // Import custom handles
    if (data.handles) {
      data.handles.forEach(handle => {
        const nodeId = this.labelToNodeId.get(handle.node);
        if (!nodeId) return;
        
        const id = createHandleId(nodeId, handle.name);
        this.labelToHandleId.set(handle.name, id);
        
        diagram.handles[id] = {
          id,
          nodeId,
          label: handle.name,
          direction: handle.direction,
          dataType: handle.dataType as DataType,
          position: handle.position,
          maxConnections: handle.maxConnections
        };
      });
    }
    
    // Import connections
    data.connections.forEach(connection => {
      const [fromNode, fromHandle] = connection.from.split(':');
      const [toNode, toHandle] = connection.to.split(':');
      
      const sourceNodeId = this.labelToNodeId.get(fromNode || '');
      const targetNodeId = this.labelToNodeId.get(toNode || '');
      
      if (!sourceNodeId || !targetNodeId) {
        console.warn(`Skipping connection ${connection.from} -> ${connection.to} due to missing nodes`);
        return;
      }
      
      // Create handle IDs from node IDs and handle names
      const sourceHandleId = createHandleId(sourceNodeId, fromHandle || 'output');
      const targetHandleId = createHandleId(targetNodeId, toHandle || 'input');
      
      const id = arrowId(generateShortId());
      const { from, to, ...arrowData } = connection;
      
      diagram.arrows[id] = {
        id,
        source: sourceHandleId,
        target: targetHandleId,
        data: arrowData
      };
    });
    
    // Add metadata
    if (data.name || data.description) {
      diagram.metadata = {
        id: generateShortId(),
        name: data.name,
        description: data.description,
        version: data.version || '2.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString()
      };
    }
    
    return diagram;
  }
}

// Export convenience functions
export const toLightYAML = (diagram: DomainDiagram): string => {
  const converter = new LightDomainConverter();
  return converter.serialize(diagram);
};

export const fromLightYAML = (yamlString: string): DomainDiagram => {
  const converter = new LightDomainConverter();
  return converter.deserialize(yamlString);
};