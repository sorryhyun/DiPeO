/**
 * JSON format converter for DiPeO diagrams
 * 
 * Handles export/import of diagrams to/from JSON format with version support
 */

import {
  DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  PersonID, ApiKeyID,
  createHandleId,
  NodeKind, LLMService,
  generateNodeId, generateShortId,
  arrowId, personId, apiKeyId
} from '@/types';
import { JSON_VERSION } from '../constants';
import type { ConverterDiagram } from '../types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import { ConverterCore, BaseExportedNode, BaseExportedArrow, BaseExportedPerson, BaseExportedApiKey, BaseExportedHandle } from '../core/converterCore';

// Export format types (extend base types)
export type ExportedNode = BaseExportedNode;
export type ExportedArrow = BaseExportedArrow;
export type ExportedPerson = BaseExportedPerson;
export type ExportedApiKey = BaseExportedApiKey;
export type ExportedHandle = BaseExportedHandle;

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

export class JsonConverter extends ConverterCore<ExportFormat> {
  /**
   * Serialize diagram to JSON string
   */
  serialize(diagram: ConverterDiagram): string {
    const exportData = this.toExportFormat(diagram);
    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Export diagram to JSON format (legacy method name)
   */
  toJSON(diagram: ConverterDiagram): string {
    return this.serialize(diagram);
  }

  /**
   * Deserialize diagram from JSON string
   */
  deserialize(jsonString: string): ConverterDiagram {
    const data = JSON.parse(jsonString) as ExportFormat;
    return this.fromExportFormat(data);
  }

  /**
   * Import diagram from JSON format (legacy method name)
   */
  fromJSON(jsonString: string): ConverterDiagram {
    return this.deserialize(jsonString);
  }

  /**
   * Convert diagram to export format
   */
  toExportFormat(diagram: ConverterDiagram): ExportFormat {
    // Clear previous state
    this.reset();
    
    // First convert API keys (needed for person references)
    const apiKeys = diagram.apiKeys.map(key => this.convertApiKeyToBase(key));
    
    // Then convert persons (may reference API keys)
    const persons = diagram.persons.map(person => this.convertPersonToBase(person));
    
    // Convert nodes
    const nodes = diagram.nodes.map(node => this.convertNodeToBase(node));
    
    // Convert arrows (references nodes)
    const arrows = diagram.arrows
      .map(arrow => this.convertArrowToBase(arrow, diagram.nodes))
      .filter((arrow): arrow is ExportedArrow => arrow !== null);
    
    // Convert handles (references nodes)
    const handles = diagram.handles
      .map(handle => this.convertHandleToBase(handle))
      .filter((handle): handle is ExportedHandle => handle !== null);
    
    return {
      version: JSON_VERSION,
      name: diagram.name,
      description: diagram.description,
      nodes,
      arrows,
      persons,
      apiKeys,
      handles
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
    this.reset();
    
    // Import in order of dependencies
    const apiKeys = this.importApiKeys(data.apiKeys || []);
    const persons = this.importPersons(data.persons || [], apiKeys);
    const nodes = this.importNodes(data.nodes || [], persons);
    const handles = this.importHandles(data.handles || [], nodes);
    const arrows = this.importArrows(data.arrows || []);
    
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

  /**
   * Override convertNodeToBase to handle person label replacement and position rounding
   */
  protected convertNodeToBase(node: DomainNode): BaseExportedNode {
    const base = super.convertNodeToBase(node);
    
    // Remove the label from data (it's already in the top-level label field)
    const { label: _, ...dataWithoutLabel } = base.data;
    
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
      ...base,
      position: {
        x: this.roundPosition(base.position.x),
        y: this.roundPosition(base.position.y)
      },
      data
    };
  }

  // Private helper methods
  
  private roundPosition(value: number): number {
    return Math.round(value);
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
      
      // Store label in data for consistency
      data.label = node.label;
      
      this.nodeLabelToId.set(node.label, id);
      
      return {
        id,
        type: node.type as NodeKind,
        position: { ...node.position },
        data
      };
    });
  }

  private importArrows(arrows: ExportedArrow[]): DomainArrow[] {
    return arrows.map(arrow => {
      const sourceNodeId = this.nodeLabelToId.get(arrow.sourceNode);
      const targetNodeId = this.nodeLabelToId.get(arrow.targetNode);
      
      if (!sourceNodeId || !targetNodeId) {
        throw new Error(`Arrow references unknown node: ${arrow.sourceNode} -> ${arrow.targetNode}`);
      }
      
      const sourceHandleId = createHandleId(sourceNodeId, arrow.sourceHandle);
      const targetHandleId = createHandleId(targetNodeId, arrow.targetHandle);
      
      return {
        id: arrowId(generateShortId()),
        source: sourceHandleId,
        target: targetHandleId,
        data: arrow.data || {}
      };
    });
  }

  private importPersons(persons: ExportedPerson[], apiKeys: DomainApiKey[]): DomainPerson[] {
    const apiKeyLabelMap = new Map<string, ApiKeyID>();
    apiKeys.forEach(key => {
      apiKeyLabelMap.set(key.name, key.id);
    });

    return persons.map(person => {
      const id = personId(generateShortId());
      
      // Find API key ID if label is provided
      let apiKeyId: ApiKeyID | undefined;
      if (person.apiKeyLabel) {
        apiKeyId = apiKeyLabelMap.get(person.apiKeyLabel);
      }
      
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
        presencePenalty: person.presencePenalty,
        apiKeyId
      };
    });
  }

  private importApiKeys(apiKeys: ExportedApiKey[]): DomainApiKey[] {
    return apiKeys.map(apiKey => {
      const id = apiKeyId(generateShortId());
      this.apiKeyLabelToId.set(apiKey.label, id);
      
      return {
        id,
        name: apiKey.label,
        service: apiKey.service as LLMService
      };
    });
  }

  private importHandles(handles: ExportedHandle[] | undefined, nodes: DomainNode[]): DomainHandle[] {
    if (!handles || handles.length === 0) {
      // Generate default handles from registry for backward compatibility
      const allHandles: DomainHandle[] = [];
      nodes.forEach(node => {
        const defaultHandles = generateNodeHandlesFromRegistry(node.type as NodeKind, node.id);
        allHandles.push(...defaultHandles);
      });
      return allHandles;
    }

    return handles.map(handle => {
      const nodeId = this.nodeLabelToId.get(handle.nodeLabel);
      if (!nodeId) {
        throw new Error(`Handle references unknown node: ${handle.nodeLabel}`);
      }
      
      const id = createHandleId(nodeId, handle.name);
      
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
}