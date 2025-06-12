/**
 * Native YAML format converter for DiPeO diagrams
 * 
 * Provides a reduced, cleaner YAML format that's more readable than JSON
 * while maintaining all necessary information for diagram reconstruction
 */

import { stringify, parse } from 'yaml';
import {
  DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  PersonID, ApiKeyID,
  createHandleId,
  NodeKind, LLMService, DataType,
  generateNodeId, generateShortId,
  arrowId, personId, apiKeyId
} from '@/types';
import { YAML_VERSION, YAML_STRINGIFY_OPTIONS } from '../constants';
import type { ConverterDiagram } from '../types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import { ConverterCore, BaseExportedNode, BaseExportedArrow, BaseExportedPerson, BaseExportedApiKey, BaseExportedHandle } from '../core/converterCore';

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

export class YamlConverter extends ConverterCore<ReducedYamlFormat> {
  /**
   * Serialize diagram to reduced YAML string
   */
  serialize(diagram: ConverterDiagram): string {
    const yamlData = this.toReducedYamlFormat(diagram);
    return stringify(yamlData, YAML_STRINGIFY_OPTIONS);
  }

  /**
   * Deserialize diagram from reduced YAML string
   */
  deserialize(yamlString: string): ConverterDiagram {
    const data = parse(yamlString) as ReducedYamlFormat;
    return this.fromReducedYamlFormat(data);
  }

  /**
   * Convert diagram to reduced YAML format
   */
  private toReducedYamlFormat(diagram: ConverterDiagram): ReducedYamlFormat {
    // Clear previous state
    this.reset();
    
    // Convert entities
    const nodes: Record<string, ReducedYamlNode> = {};
    const connections: ReducedYamlArrow[] = [];
    const persons: Record<string, ReducedYamlPerson> = {};
    const apiKeys: Record<string, ReducedYamlApiKey> = {};
    const handles: ReducedYamlHandle[] = [];
    
    // Convert API keys first
    diagram.apiKeys.forEach(key => {
      const base = this.convertApiKeyToBase(key);
      apiKeys[base.label] = {
        service: base.service
      };
    });
    
    // Convert persons
    diagram.persons.forEach(person => {
      const base = this.convertPersonToBase(person);
      const reducedPerson: ReducedYamlPerson = {
        model: base.model
      };
      
      // Only add non-default values
      if (base.service !== 'openai') reducedPerson.service = base.service;
      if (base.apiKeyLabel) reducedPerson.apiKey = base.apiKeyLabel;
      if (base.systemPrompt) reducedPerson.systemPrompt = base.systemPrompt;
      if (base.temperature !== undefined && base.temperature !== 0.2) reducedPerson.temperature = base.temperature;
      if (base.maxTokens) reducedPerson.maxTokens = base.maxTokens;
      if (base.topP !== undefined && base.topP !== 1) reducedPerson.topP = base.topP;
      if (base.frequencyPenalty) reducedPerson.frequencyPenalty = base.frequencyPenalty;
      if (base.presencePenalty) reducedPerson.presencePenalty = base.presencePenalty;
      
      persons[base.label] = reducedPerson;
    });
    
    // Convert nodes
    diagram.nodes.forEach(node => {
      const base = this.convertNodeToBase(node);
      const { label, ...dataWithoutLabel } = base.data;
      
      // Create reduced node with flattened data
      const reducedNode: ReducedYamlNode = {
        label: base.label,
        type: base.type,
        position: {
          x: Math.round(base.position.x),
          y: Math.round(base.position.y)
        }
      };
      
      // Add data fields directly to node (except internal fields)
      Object.entries(dataWithoutLabel).forEach(([key, value]) => {
        // Skip internal/computed fields
        if (key === 'id' || key === 'handles' || key === 'type') return;
        
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
      
      nodes[base.label] = reducedNode;
    });
    
    // Convert arrows
    diagram.arrows.forEach(arrow => {
      const base = this.convertArrowToBase(arrow, diagram.nodes);
      if (!base) return;
      
      const reducedArrow: ReducedYamlArrow = {
        from: `${base.sourceNode}:${base.sourceHandle}`,
        to: `${base.targetNode}:${base.targetHandle}`
      };
      
      // Add data fields if present
      if (base.data && Object.keys(base.data).length > 0) {
        Object.entries(base.data).forEach(([key, value]) => {
          reducedArrow[key] = value;
        });
      }
      
      connections.push(reducedArrow);
    });
    
    // Convert handles (only custom ones)
    if (diagram.handles && diagram.handles.length > 0) {
      diagram.handles.forEach(handle => {
        const base = this.convertHandleToBase(handle);
        if (!base) return;
        
        // Skip default handles that would be auto-generated
        const node = diagram.nodes.find(n => n.id === handle.nodeId);
        if (node) {
          const defaultHandles = generateNodeHandlesFromRegistry(node.type as NodeKind, node.id);
          const isDefault = defaultHandles.some(dh => 
            dh.label === handle.label &&
            dh.direction === handle.direction &&
            dh.dataType === handle.dataType &&
            dh.position === handle.position
          );
          if (isDefault) return;
        }
        
        handles.push({
          node: base.nodeLabel,
          name: base.label,
          direction: base.direction,
          dataType: base.dataType,
          position: base.position || 'bottom',
          maxConnections: base.maxConnections
        });
      });
    }
    
    // Build final format
    const result: ReducedYamlFormat = {
      version: YAML_VERSION,
      nodes,
      connections
    };
    
    // Only add optional fields if they have content
    if (diagram.name) result.name = diagram.name;
    if (diagram.description) result.description = diagram.description;
    if (Object.keys(persons).length > 0) result.persons = persons;
    if (Object.keys(apiKeys).length > 0) result.apiKeys = apiKeys;
    if (handles.length > 0) result.handles = handles;
    
    return result;
  }

  /**
   * Convert from reduced YAML format to diagram
   */
  private fromReducedYamlFormat(data: ReducedYamlFormat): ConverterDiagram {
    // Validate the data
    const validation = this.validateReducedYamlData(data);
    if (!validation.valid) {
      throw new Error(`Invalid YAML data: ${validation.errors.join(', ')}`);
    }
    
    // Clear previous state
    this.reset();
    
    // Import API keys
    const apiKeys: DomainApiKey[] = [];
    if (data.apiKeys) {
      Object.entries(data.apiKeys).forEach(([label, apiKey]) => {
        const id = apiKeyId(generateShortId());
        this.apiKeyLabelToId.set(label, id);
        apiKeys.push({
          id,
          label,
          service: apiKey.service as LLMService
        });
      });
    }
    
    // Import persons
    const persons: DomainPerson[] = [];
    if (data.persons) {
      Object.entries(data.persons).forEach(([label, person]) => {
        const id = personId(generateShortId());
        this.personLabelToId.set(label, id);
        
        // Find API key ID if label is provided
        let apiKeyId: ApiKeyID | undefined;
        if (person.apiKey) {
          apiKeyId = this.apiKeyLabelToId.get(person.apiKey);
        }
        
        persons.push({
          id,
          label,
          model: person.model,
          service: (person.service || 'openai') as LLMService,
          systemPrompt: person.systemPrompt,
          temperature: person.temperature ?? 0.7,
          maxTokens: person.maxTokens,
          topP: person.topP ?? 1,
          frequencyPenalty: person.frequencyPenalty ?? 0,
          presencePenalty: person.presencePenalty ?? 0,
          apiKeyId
        });
      });
    }
    
    // Import nodes
    const nodes: DomainNode[] = [];
    Object.entries(data.nodes).forEach(([nodeLabel, node]) => {
      const id = generateNodeId();
      this.nodeLabelToId.set(nodeLabel, id);
      
      // Extract node data
      const { label, type, position, person, ...otherData } = node;
      const nodeData: any = {
        label: nodeLabel,
        ...otherData
      };
      
      // Convert person label back to ID
      if (person) {
        const personId = this.personLabelToId.get(person);
        if (personId) {
          nodeData.personId = personId;
        }
      }
      
      nodes.push({
        id,
        type: type as NodeKind,
        position: { ...position },
        data: nodeData
      });
    });
    
    // Import handles
    const handles: DomainHandle[] = [];
    if (data.handles && data.handles.length > 0) {
      // Import custom handles
      data.handles.forEach(handle => {
        const nodeId = this.nodeLabelToId.get(handle.node);
        if (!nodeId) {
          throw new Error(`Handle references unknown node: ${handle.node}`);
        }
        
        handles.push({
          id: createHandleId(nodeId, handle.name),
          nodeId,
          label: handle.name,
          direction: handle.direction,
          dataType: handle.dataType as DataType,
          position: handle.position,
          maxConnections: handle.maxConnections
        });
      });
    }
    
    // Generate default handles for all nodes
    nodes.forEach(node => {
      const defaultHandles = generateNodeHandlesFromRegistry(node.type as NodeKind, node.id);
      // Add default handles that aren't already defined
      defaultHandles.forEach(dh => {
        const exists = handles.some(h => 
          h.nodeId === dh.nodeId && 
          h.label === dh.label
        );
        if (!exists) {
          handles.push(dh);
        }
      });
    });
    
    // Import arrows
    const arrows: DomainArrow[] = [];
    data.connections.forEach(conn => {
      const [sourceNodeLabel, sourceHandleName] = conn.from.split(':');
      const [targetNodeLabel, targetHandleName] = conn.to.split(':');
      
      const sourceNodeId = this.nodeLabelToId.get(sourceNodeLabel || '');
      const targetNodeId = this.nodeLabelToId.get(targetNodeLabel || '');
      
      if (!sourceNodeId || !targetNodeId) {
        throw new Error(`Connection references unknown node: ${conn.from} -> ${conn.to}`);
      }
      
      const sourceHandleId = createHandleId(sourceNodeId, sourceHandleName || 'output');
      const targetHandleId = createHandleId(targetNodeId, targetHandleName || 'input');
      
      const { from, to, label, ...otherData } = conn;
      
      arrows.push({
        id: arrowId(generateShortId()),
        source: sourceHandleId,
        target: targetHandleId,
        data: { label, ...otherData } as any
      });
    });
    
    return {
      id: `diagram-${generateShortId()}`,
      name: data.name || 'Imported Diagram',
      description: data.description,
      nodes,
      arrows,
      persons,
      apiKeys,
      handles
    };
  }

  /**
   * Validate reduced YAML data
   */
  private validateReducedYamlData(data: unknown): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!data || typeof data !== 'object') {
      errors.push('Data must be an object');
      return { valid: false, errors };
    }

    const yamlData = data as ReducedYamlFormat;

    // Check version
    if (!yamlData.version) {
      errors.push('Missing version field');
    }

    // Check required fields
    if (!yamlData.nodes || typeof yamlData.nodes !== 'object') {
      errors.push('nodes must be an object');
    }
    if (!Array.isArray(yamlData.connections)) {
      errors.push('connections must be an array');
    }

    // Validate nodes
    if (yamlData.nodes && typeof yamlData.nodes === 'object') {
      Object.entries(yamlData.nodes).forEach(([label, node]) => {
        if (!node.type) errors.push(`Node ${label} missing type`);
        if (!node.position || typeof node.position.x !== 'number' || typeof node.position.y !== 'number') {
          errors.push(`Node ${label} missing valid position`);
        }
      });
    }

    // Validate connections
    if (Array.isArray(yamlData.connections)) {
      yamlData.connections.forEach((conn, index) => {
        if (!conn.from || !conn.from.includes(':')) {
          errors.push(`Connection ${index} missing valid 'from' (format: nodeLabel:handleName)`);
        }
        if (!conn.to || !conn.to.includes(':')) {
          errors.push(`Connection ${index} missing valid 'to' (format: nodeLabel:handleName)`);
        }
      });
    }

    return { valid: errors.length === 0, errors };
  }
}

// Legacy static class for backward compatibility
export class Yaml {
  private static converter = new YamlConverter();

  static toYAML(diagram: ConverterDiagram): string {
    return this.converter.serialize(diagram);
  }

  static fromYAML(yamlString: string): ConverterDiagram {
    return this.converter.deserialize(yamlString);
  }
}