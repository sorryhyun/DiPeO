/**
 * JSON format converter for DiPeO diagrams
 * 
 * Handles export/import of diagrams to/from JSON format with version support
 */

import {
  DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  NodeID, PersonID, ApiKeyID, HandleID,
  parseHandleId, createHandleId,
  NodeKind, DataType, HandlePosition, LLMService,
  generateNodeId, generateShortId,
  nodeId, arrowId, personId, apiKeyId, handleId
} from '@/types';
import { JSON_VERSION } from '../constants';
import type { ConverterDiagram } from '../types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import { isValidHandleName } from '@/utils/node/handle-utils';

// Export format types
export interface ExportedNode {
  label: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface ExportedArrow {
  sourceNode: string;
  sourceHandle: string;
  targetNode: string;
  targetHandle: string;
  data?: Record<string, unknown>;
}

export interface ExportedPerson {
  label: string;
  model: string;
  service: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  apiKeyLabel?: string;
}

export interface ExportedApiKey {
  label: string;
  service: string;
}

export interface ExportedHandle {
  nodeLabel: string;
  name: string;
  direction: 'input' | 'output';
  dataType: DataType;
  position?: HandlePosition;
  label?: string;
  maxConnections?: number;
}

export interface ExportFormat {
  version: string;
  name: string;
  description?: string;
  nodes: ExportedNode[];
  arrows: ExportedArrow[];
  persons: ExportedPerson[];
  apiKeys: ExportedApiKey[];
  handles?: ExportedHandle[];
}

export class JsonConverter {
  // Label tracking for uniqueness
  private usedNodeLabels = new Set<string>();
  private usedPersonLabels = new Set<string>();
  private usedApiKeyLabels = new Set<string>();
  
  // ID to label mappings for export
  private nodeIdToLabel = new Map<NodeID, string>();
  private personIdToLabel = new Map<PersonID, string>();
  private apiKeyIdToLabel = new Map<ApiKeyID, string>();
  
  // Label to ID mappings for import
  private nodeLabelToId = new Map<string, NodeID>();
  private personLabelToId = new Map<string, PersonID>();
  private apiKeyLabelToId = new Map<string, ApiKeyID>();

  /**
   * Export diagram to JSON format
   */
  toJSON(diagram: ConverterDiagram): string {
    const exportData = this.toExportFormat(diagram);
    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Import diagram from JSON format
   */
  fromJSON(jsonString: string): ConverterDiagram {
    const data = JSON.parse(jsonString) as ExportFormat;
    return this.fromExportFormat(data);
  }

  /**
   * Convert diagram to export format
   */
  toExportFormat(diagram: ConverterDiagram): ExportFormat {
    // Clear previous state
    this.clearMappings();
    
    // Build mappings
    this.buildExportMappings(diagram);
    
    return {
      version: JSON_VERSION,
      name: diagram.name,
      description: diagram.description,
      nodes: this.exportNodes(diagram.nodes),
      arrows: this.exportArrows(diagram.arrows),
      persons: this.exportPersons(diagram.persons),
      apiKeys: this.exportApiKeys(diagram.apiKeys),
      handles: this.exportHandles(diagram.handles)
    };
  }

  /**
   * Convert from export format to diagram
   */
  fromExportFormat(data: ExportFormat): ConverterDiagram {
    // Validate the data
    const validation = this.validateExportData(data);
    if (!validation.valid) {
      throw new Error(`Invalid export data: ${validation.errors.join(', ')}`);
    }
    
    // Clear previous state
    this.clearMappings();
    
    // Import in order of dependencies
    const apiKeys = this.importApiKeys(data.apiKeys || []);
    const persons = this.importPersons(data.persons || [], apiKeys);
    const nodes = this.importNodes(data.nodes || [], persons);
    const handles = this.importHandles(data.handles || [], nodes);
    const arrows = this.importArrows(data.arrows || [], nodes);
    
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
   * Validate export data
   */
  validateExportData(data: unknown): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!data || typeof data !== 'object') {
      errors.push('Data must be an object');
      return { valid: false, errors };
    }

    const exportData = data as ExportFormat;

    // Check version
    if (!exportData.version) {
      errors.push('Missing version field');
    }

    // Check required arrays
    if (!Array.isArray(exportData.nodes)) {
      errors.push('nodes must be an array');
    }
    if (!Array.isArray(exportData.arrows)) {
      errors.push('arrows must be an array');
    }
    if (!Array.isArray(exportData.persons)) {
      errors.push('persons must be an array');
    }
    if (!Array.isArray(exportData.apiKeys)) {
      errors.push('apiKeys must be an array');
    }
    
    // Check handles array for v4.0.0+
    if (exportData.version && exportData.version >= '4.0.0') {
      if (!Array.isArray(exportData.handles)) {
        errors.push('handles must be an array for version 4.0.0+');
      }
    }

    // Validate nodes
    if (Array.isArray(exportData.nodes)) {
      exportData.nodes.forEach((node, index) => {
        if (!node.label) errors.push(`Node ${index} missing label`);
        if (!node.type) errors.push(`Node ${index} missing type`);
        if (!node.position || typeof node.position.x !== 'number' || typeof node.position.y !== 'number') {
          errors.push(`Node ${index} missing valid position`);
        }
      });
    }

    // Validate arrows
    if (Array.isArray(exportData.arrows)) {
      exportData.arrows.forEach((arrow, index) => {
        if (!arrow.sourceNode) errors.push(`Arrow ${index} missing sourceNode`);
        if (!arrow.sourceHandle) errors.push(`Arrow ${index} missing sourceHandle`);
        if (!arrow.targetNode) errors.push(`Arrow ${index} missing targetNode`);
        if (!arrow.targetHandle) errors.push(`Arrow ${index} missing targetHandle`);
      });
    }

    return { valid: errors.length === 0, errors };
  }

  // Private helper methods

  private clearMappings(): void {
    this.usedNodeLabels.clear();
    this.usedPersonLabels.clear();
    this.usedApiKeyLabels.clear();
    this.nodeIdToLabel.clear();
    this.personIdToLabel.clear();
    this.apiKeyIdToLabel.clear();
    this.nodeLabelToId.clear();
    this.personLabelToId.clear();
    this.apiKeyLabelToId.clear();
  }

  private buildExportMappings(diagram: ConverterDiagram): void {
    // Build node label mappings
    diagram.nodes.forEach(node => {
      const label = (node.data.label as string) || node.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedNodeLabels);
      this.nodeIdToLabel.set(node.id, uniqueLabel);
    });

    // Build person label mappings
    diagram.persons.forEach(person => {
      const label = person.label || person.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedPersonLabels);
      this.personIdToLabel.set(person.id, uniqueLabel);
    });

    // Build API key label mappings
    diagram.apiKeys.forEach(apiKey => {
      const label = apiKey.name || apiKey.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedApiKeyLabels);
      this.apiKeyIdToLabel.set(apiKey.id, uniqueLabel);
    });
  }

  private ensureUniqueLabel(baseLabel: string, usedLabels: Set<string>): string {
    if (!usedLabels.has(baseLabel)) {
      usedLabels.add(baseLabel);
      return baseLabel;
    }

    // Try alphabetic suffixes: -a, -b, -c, etc.
    for (let i = 0; i < 26; i++) {
      const suffix = String.fromCharCode(97 + i); // a-z
      const candidateLabel = `${baseLabel}-${suffix}`;
      if (!usedLabels.has(candidateLabel)) {
        usedLabels.add(candidateLabel);
        return candidateLabel;
      }
    }

    // Fallback to numeric suffixes if all alphabetic are taken
    let counter = 1;
    let uniqueLabel = `${baseLabel}-${counter}`;
    while (usedLabels.has(uniqueLabel)) {
      counter++;
      uniqueLabel = `${baseLabel}-${counter}`;
    }
    usedLabels.add(uniqueLabel);
    return uniqueLabel;
  }

  private roundPosition(value: number): number {
    return Math.round(value);
  }

  private exportNodes(nodes: DomainNode[]): ExportedNode[] {
    return nodes.map(node => {
      const label = this.nodeIdToLabel.get(node.id) || node.id;

      // Prepare data without internal properties
      const { label: _, ...dataWithoutLabel } = node.data;

      // Replace person ID with label if exists
      const data = { ...dataWithoutLabel };
      if ('personId' in data && data.personId) {
        const personLabel = this.personIdToLabel.get(data.personId as PersonID);
        if (personLabel) {
          data.personLabel = personLabel;
          delete data.personId;
        }
      }

      return {
        label,
        type: node.type,
        position: {
          x: this.roundPosition(node.position.x),
          y: this.roundPosition(node.position.y)
        },
        data
      };
    });
  }

  private exportArrows(arrows: DomainArrow[]): ExportedArrow[] {
    return arrows.map(arrow => {
      const { nodeId: sourceNodeId, handleName: sourceHandleName } = parseHandleId(arrow.source);
      const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);
      
      const sourceNode = this.nodeIdToLabel.get(sourceNodeId) || sourceNodeId;
      const targetNode = this.nodeIdToLabel.get(targetNodeId) || targetNodeId;

      return {
        sourceNode,
        sourceHandle: sourceHandleName,
        targetNode,
        targetHandle: targetHandleName,
        data: arrow.data
      };
    });
  }

  private exportPersons(persons: DomainPerson[]): ExportedPerson[] {
    return persons.map(person => {
      const label = this.personIdToLabel.get(person.id) || person.id;
      
      const exported: ExportedPerson = {
        label,
        model: person.model,
        service: person.service
      };

      // Add optional fields if they exist
      if (person.systemPrompt) exported.systemPrompt = person.systemPrompt;
      if (person.temperature !== undefined) exported.temperature = person.temperature;
      if (person.maxTokens !== undefined) exported.maxTokens = person.maxTokens;
      if (person.topP !== undefined) exported.topP = person.topP;
      if (person.frequencyPenalty !== undefined) exported.frequencyPenalty = person.frequencyPenalty;
      if (person.presencePenalty !== undefined) exported.presencePenalty = person.presencePenalty;

      return exported;
    });
  }

  private exportApiKeys(apiKeys: DomainApiKey[]): ExportedApiKey[] {
    return apiKeys.map(apiKey => {
      const label = this.apiKeyIdToLabel.get(apiKey.id) || apiKey.id;
      return {
        label,
        service: apiKey.service
      };
    });
  }

  private exportHandles(handles: DomainHandle[]): ExportedHandle[] {
    return handles.map(handle => {
      const nodeLabel = this.nodeIdToLabel.get(handle.nodeId) || handle.nodeId;
      
      const exportedHandle: ExportedHandle = {
        nodeLabel,
        name: handle.name,
        direction: handle.direction,
        dataType: handle.dataType
      };

      // Add optional fields
      if (handle.position) exportedHandle.position = handle.position;
      if (handle.label) exportedHandle.label = handle.label;
      if (handle.maxConnections !== undefined) exportedHandle.maxConnections = handle.maxConnections;

      return exportedHandle;
    });
  }

  private importNodes(nodes: ExportedNode[], persons: DomainPerson[]): DomainNode[] {
    const personLabelMap = new Map<string, PersonID>();
    persons.forEach(person => {
      personLabelMap.set(person.label, person.id);
    });

    return nodes.map(node => {
      const id = generateNodeId();
      const data = { ...node.data };
      
      // Convert person label back to ID
      if ('personLabel' in data && data.personLabel) {
        const personId = personLabelMap.get(data.personLabel as string);
        if (personId) {
          data.personId = personId;
          delete data.personLabel;
        }
      }

      // Ensure label is set
      data.label = node.label;

      // Store mapping
      this.nodeLabelToId.set(node.label, id);

      return {
        id,
        type: node.type as NodeKind,
        position: node.position,
        data
      };
    });
  }

  private importArrows(arrows: ExportedArrow[], nodes: DomainNode[]): DomainArrow[] {
    // Create a map of node IDs to node types for validation
    const nodeTypeMap = new Map<NodeID, NodeKind>();
    nodes.forEach(node => nodeTypeMap.set(node.id, node.type));
    
    return arrows.map((arrow, index) => {
      const sourceNodeId = this.nodeLabelToId.get(arrow.sourceNode);
      const targetNodeId = this.nodeLabelToId.get(arrow.targetNode);
      
      if (!sourceNodeId || !targetNodeId) {
        throw new Error(`Invalid arrow reference: ${arrow.sourceNode} -> ${arrow.targetNode}`);
      }

      // Validate handle names are valid for the node types
      const sourceNodeType = nodeTypeMap.get(sourceNodeId);
      const targetNodeType = nodeTypeMap.get(targetNodeId);
      
      if (sourceNodeType && !isValidHandleName(sourceNodeType, arrow.sourceHandle, 'output')) {
        throw new Error(`Arrow ${index}: Invalid output handle "${arrow.sourceHandle}" for ${sourceNodeType} node "${arrow.sourceNode}"`);
      }
      
      if (targetNodeType && !isValidHandleName(targetNodeType, arrow.targetHandle, 'input')) {
        throw new Error(`Arrow ${index}: Invalid input handle "${arrow.targetHandle}" for ${targetNodeType} node "${arrow.targetNode}"`);
      }

      const sourceHandleId = createHandleId(sourceNodeId, arrow.sourceHandle);
      const targetHandleId = createHandleId(targetNodeId, arrow.targetHandle);

      return {
        id: arrowId(`arrow-${generateShortId()}`),
        source: sourceHandleId,
        target: targetHandleId,
        data: arrow.data
      };
    });
  }

  private importPersons(persons: ExportedPerson[], apiKeys: DomainApiKey[]): DomainPerson[] {
    const apiKeyLabelMap = new Map<string, ApiKeyID>();
    apiKeys.forEach(key => {
      apiKeyLabelMap.set(key.name, key.id);
    });

    return persons.map(person => {
      const id = personId(`person-${generateShortId()}`);
      
      // Store mapping
      this.personLabelToId.set(person.label, id);

      return {
        id,
        label: person.label,
        model: person.model,
        service: person.service as LLMService,
        systemPrompt: person.systemPrompt,
        temperature: person.temperature,
        maxTokens: person.maxTokens,
        topP: person.topP,
        frequencyPenalty: person.frequencyPenalty,
        presencePenalty: person.presencePenalty
      };
    });
  }

  private importApiKeys(apiKeys: ExportedApiKey[]): DomainApiKey[] {
    return apiKeys.map(apiKey => {
      const id = apiKeyId(`apikey-${generateShortId()}`);
      
      // Store mapping
      this.apiKeyLabelToId.set(apiKey.label, id);

      return {
        id,
        name: apiKey.label,
        service: apiKey.service as DomainApiKey['service']
      };
    });
  }

  private importHandles(handles: ExportedHandle[] | undefined, nodes: DomainNode[]): DomainHandle[] {
    if (!handles || handles.length === 0) {
      // Generate handles from node configurations
      return this.generateHandlesFromNodes(nodes);
    }

    return handles.map(handle => {
      const nodeId = this.nodeLabelToId.get(handle.nodeLabel);
      if (!nodeId) {
        throw new Error(`Invalid handle reference: node ${handle.nodeLabel} not found`);
      }

      const id = handleId(nodeId, handle.name);
      
      return {
        id,
        nodeId,
        name: handle.name,
        direction: handle.direction,
        dataType: handle.dataType,
        position: handle.position,
        label: handle.label,
        maxConnections: handle.maxConnections
      };
    });
  }

  private generateHandlesFromNodes(nodes: DomainNode[]): DomainHandle[] {
    const handles: DomainHandle[] = [];
    
    // Generate handles for each node based on its type
    nodes.forEach(node => {
      const nodeHandles = generateNodeHandlesFromRegistry(node.id, node.type);
      handles.push(...nodeHandles);
    });
    
    return handles;
  }
}

// Convenience functions
export function toJSON(diagram: ConverterDiagram): string {
  const converter = new JsonConverter();
  return converter.toJSON(diagram);
}

export function fromJSON(jsonString: string): ConverterDiagram {
  const converter = new JsonConverter();
  return converter.fromJSON(jsonString);
}

export function toExportFormat(diagram: ConverterDiagram): ExportFormat {
  const converter = new JsonConverter();
  return converter.toExportFormat(diagram);
}

export function fromExportFormat(data: ExportFormat): ConverterDiagram {
  const converter = new JsonConverter();
  return converter.fromExportFormat(data);
}

export function validateExportData(data: unknown): { valid: boolean; errors: string[] } {
  const converter = new JsonConverter();
  return converter.validateExportData(data);
}