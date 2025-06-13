/**
 * Human-readable YAML format converter for DiPeO diagrams
 * 
 * This format embeds connections within node definitions for better readability
 * and uses labels instead of IDs for all references
 * Works directly with DomainDiagram types
 */

import { stringify, parse } from 'yaml';
import {
  DomainDiagram, DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  NodeID, ArrowID, PersonID, ApiKeyID, HandleID,
  NodeKind, LLMService, DataType,
  generateNodeId, generateShortId, arrowId, personId, apiKeyId, handleId, createHandleId, parseHandleId
} from '@/types';
import { YAML_VERSION, YAML_STRINGIFY_OPTIONS } from '../constants';
import { DomainFormatConverter } from '../core/types';
import { generateNodeHandles } from '@/utils/node/handle-builder';
import { getNodeConfig } from '@/config';

// Readable format types
export interface ReadableConnection {
  to: string;         // nodeLabel:handleName or nodeLabel for default
  handle?: string;    // Optional source handle name
  [key: string]: any; // Additional arrow data
}

export interface ReadableNode {
  type: string;
  position: { x: number; y: number };
  connections?: ReadableConnection[];
  // Node-specific data fields
  [key: string]: any;
}

export interface ReadablePerson {
  model: string;
  service?: string;
  apiKey?: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

export interface ReadableApiKey {
  service: string;
}

export interface ReadableHandle {
  node: string;
  name: string;
  direction: 'input' | 'output';
  dataType: string;
  position?: 'left' | 'right' | 'top' | 'bottom';
  maxConnections?: number;
}

export interface ReadableDiagram {
  version: string;
  name?: string;
  description?: string;
  workflow: Record<string, ReadableNode>;
  persons?: Record<string, ReadablePerson>;
  apiKeys?: Record<string, ReadableApiKey>;
  handles?: ReadableHandle[];
}

export class ReadableDomainConverter implements DomainFormatConverter {
  readonly formatName = 'readable';
  readonly fileExtension = '.readable.yaml';

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
    const readableData = this.toReadableFormat(diagram);
    return stringify(readableData, YAML_STRINGIFY_OPTIONS);
  }

  deserialize(yamlString: string): DomainDiagram {
    const data = parse(yamlString) as ReadableDiagram;
    return this.fromReadableFormat(data);
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
   * Convert DomainDiagram to readable format
   */
  private toReadableFormat(diagram: DomainDiagram): ReadableDiagram {
    this.reset();
    
    const workflow: Record<string, ReadableNode> = {};
    const persons: Record<string, ReadablePerson> = {};
    const apiKeys: Record<string, ReadableApiKey> = {};
    const handles: ReadableHandle[] = [];
    
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
      
      const readablePerson: ReadablePerson = {
        model: person.model
      };
      
      // Only add non-default values
      if (person.service !== 'openai') readablePerson.service = person.service;
      if (person.apiKeyId) {
        const apiKeyLabel = this.apiKeyIdToLabel.get(person.apiKeyId);
        if (apiKeyLabel) readablePerson.apiKey = apiKeyLabel;
      }
      if (person.systemPrompt) readablePerson.systemPrompt = person.systemPrompt;
      if (person.temperature !== undefined && person.temperature !== 0.2) {
        readablePerson.temperature = person.temperature;
      }
      if (person.maxTokens) readablePerson.maxTokens = person.maxTokens;
      if (person.topP !== undefined && person.topP !== 1) readablePerson.topP = person.topP;
      if (person.frequencyPenalty) readablePerson.frequencyPenalty = person.frequencyPenalty;
      if (person.presencePenalty) readablePerson.presencePenalty = person.presencePenalty;
      
      persons[label] = readablePerson;
    });
    
    // Convert handles (build ID to label mapping)
    Object.entries(diagram.handles).forEach(([id, handle]) => {
      const label = handle.label || `HANDLE_${id}`;
      this.handleIdToLabel.set(id as HandleID, label);
    });
    
    // Convert nodes (build ID to label mapping)
    Object.entries(diagram.nodes).forEach(([id, node]) => {
      const label = typeof node.data.label === 'string' ? node.data.label : `NODE_${id}`;
      this.nodeIdToLabel.set(id as NodeID, label);
    });
    
    // Create nodes with embedded connections
    Object.entries(diagram.nodes).forEach(([nodeId, node]) => {
      const nodeLabel = this.nodeIdToLabel.get(nodeId as NodeID)!;
      
      const readableNode: ReadableNode = {
        type: node.type,
        position: {
          x: Math.round(node.position.x),
          y: Math.round(node.position.y)
        }
      };
      
      // Add data fields (except internal fields)
      Object.entries(node.data).forEach(([key, value]) => {
        if (key === 'id' || key === 'handles' || key === 'type' || key === 'label') return;
        
        // Replace personId with person label
        if (key === 'personId' && value) {
          const personLabel = this.personIdToLabel.get(value as PersonID);
          if (personLabel) {
            readableNode.person = personLabel;
            return;
          }
        }
        
        readableNode[key] = value;
      });
      
      // Find all outgoing connections from this node
      const connections: ReadableConnection[] = [];
      Object.values(diagram.arrows).forEach(arrow => {
        const { nodeId: sourceNodeId } = parseHandleId(arrow.source);
        if (sourceNodeId === nodeId) {
          const { nodeId: targetNodeId } = parseHandleId(arrow.target);
          const targetLabel = this.nodeIdToLabel.get(targetNodeId);
          const sourceHandleLabel = this.handleIdToLabel.get(arrow.source);
          const targetHandleLabel = this.handleIdToLabel.get(arrow.target);
          
          if (!targetLabel || !targetHandleLabel) return;
          
          const connection: ReadableConnection = {
            to: `${targetLabel}:${targetHandleLabel}`
          };
          
          // Add source handle if it's not the default output
          const defaultOutputHandle = this.findDefaultOutputHandle(node, Object.values(diagram.handles));
          if (sourceHandleLabel && arrow.source !== defaultOutputHandle?.id) {
            connection.handle = sourceHandleLabel;
          }
          
          // Add arrow data if present
          if (arrow.data && Object.keys(arrow.data).length > 0) {
            Object.assign(connection, arrow.data);
          }
          
          connections.push(connection);
        }
      });
      
      if (connections.length > 0) {
        readableNode.connections = connections;
      }
      
      workflow[nodeLabel] = readableNode;
    });
    
    // Convert custom handles only
    Object.entries(diagram.handles).forEach(([id, handle]) => {
      const nodeLabel = this.nodeIdToLabel.get(handle.nodeId);
      if (!nodeLabel) return;
      
      // Skip default handles
      const node = diagram.nodes[handle.nodeId];
      if (node) {
        const nodeConfig = getNodeConfig(node.type as NodeKind);
        const defaultHandles = nodeConfig ? generateNodeHandles(handle.nodeId, nodeConfig, node.type as NodeKind) : [];
        const isDefault = defaultHandles.some((dh: DomainHandle) => 
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
        position: handle.position,
        maxConnections: handle.maxConnections
      });
    });
    
    // Build final format
    const result: ReadableDiagram = {
      version: YAML_VERSION,
      workflow
    };
    
    // Add optional fields
    if (diagram.metadata?.name) result.name = diagram.metadata.name;
    if (diagram.metadata?.description) result.description = diagram.metadata.description;
    if (Object.keys(persons).length > 0) result.persons = persons;
    if (Object.keys(apiKeys).length > 0) result.apiKeys = apiKeys;
    if (handles.length > 0) result.handles = handles;
    
    return result;
  }

  /**
   * Convert from readable format to DomainDiagram
   */
  private fromReadableFormat(data: ReadableDiagram): DomainDiagram {
    this.reset();
    
    const diagram: DomainDiagram = {
      nodes: {},
      arrows: {},
      handles: {},
      persons: {},
      apiKeys: {}
    };
    
    // Import API keys
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
    Object.entries(data.workflow).forEach(([label, node]) => {
      const nodeId = generateNodeId();
      this.labelToNodeId.set(label, nodeId);
      
      const nodeData: any = {
        id: nodeId,
        label,
        ...node
      };
      
      // Remove non-data fields
      delete nodeData.type;
      delete nodeData.position;
      delete nodeData.connections;
      
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
        type: node.type as NodeKind,
        position: node.position,
        data: nodeData
      };
    });
    
    // Generate default handles
    Object.values(diagram.nodes).forEach(node => {
      const nodeConfig = getNodeConfig(node.type as NodeKind);
      if (nodeConfig) {
        const handles = generateNodeHandles(node.id, nodeConfig, node.type as NodeKind);
        handles.forEach((handle: DomainHandle) => {
          this.labelToHandleId.set(handle.label, handle.id);
          diagram.handles[handle.id] = handle;
        });
      }
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
          position: handle.position || 'bottom',
          maxConnections: handle.maxConnections
        };
      });
    }
    
    // Import connections from workflow nodes
    Object.entries(data.workflow).forEach(([sourceLabel, node]) => {
      if (!node.connections) return;
      
      const sourceNodeId = this.labelToNodeId.get(sourceLabel);
      if (!sourceNodeId) return;
      
      node.connections.forEach(connection => {
        const parts = connection.to.split(':');
        const targetLabel = parts[0] || '';
        const targetHandleName = parts[1] || 'input';
        const targetNodeId = this.labelToNodeId.get(targetLabel);
        const targetHandleId = this.labelToHandleId.get(targetHandleName);
        
        if (!targetNodeId || !targetHandleId) {
          console.warn(`Skipping connection to ${connection.to}: target not found`);
          return;
        }
        
        // Determine source handle
        let sourceHandleId: HandleID | undefined;
        if (connection.handle) {
          sourceHandleId = this.labelToHandleId.get(connection.handle);
        } else {
          // Use default output handle
          const sourceNode = diagram.nodes[sourceNodeId];
          if (sourceNode) {
            const defaultHandle = this.findDefaultOutputHandle(
              sourceNode,
              Object.values(diagram.handles)
            );
            sourceHandleId = defaultHandle?.id;
          }
        }
        
        if (!sourceHandleId) {
          console.warn(`Skipping connection from ${sourceLabel}: no valid source handle`);
          return;
        }
        
        const id = arrowId(generateShortId());
        const { to, handle, ...arrowData } = connection;
        
        diagram.arrows[id] = {
          id,
          source: sourceHandleId,
          target: targetHandleId,
          data: Object.keys(arrowData).length > 0 ? arrowData : undefined
        };
      });
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

  /**
   * Find the default output handle for a node
   */
  private findDefaultOutputHandle(
    node: DomainNode,
    handles: DomainHandle[]
  ): DomainHandle | undefined {
    const nodeHandles = handles.filter(h => h.nodeId === node.id && h.direction === 'output');
    
    // Look for explicitly marked default or 'output' named handle
    return nodeHandles.find(h => h.label === 'output' || h.label === 'default') || 
           nodeHandles[0];
  }
}

// Export convenience functions
export const toReadableYAML = (diagram: DomainDiagram): string => {
  const converter = new ReadableDomainConverter();
  return converter.serialize(diagram);
};

export const fromReadableYAML = (yamlString: string): DomainDiagram => {
  const converter = new ReadableDomainConverter();
  return converter.deserialize(yamlString);
};