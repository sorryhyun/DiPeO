/**
 * Abstract base class for diagram format converters
 * 
 * Provides common functionality for label tracking, ID mappings,
 * and basic conversion logic shared between JSON and YAML converters
 */

import {
  DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  NodeID, PersonID, ApiKeyID, HandleID, ArrowID,
  parseHandleId, createHandleId,
  NodeKind, DataType, HandlePosition, LLMService,
  generateNodeId, generateShortId,
  nodeId, arrowId, personId, apiKeyId, handleId
} from '@/types';
import type { ConverterDiagram } from '../types';

// Base export types that can be extended by specific formats
export interface BaseExportedNode {
  label: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface BaseExportedArrow {
  sourceNode: string;
  sourceHandle: string;
  targetNode: string;
  targetHandle: string;
  data?: Record<string, unknown>;
}

export interface BaseExportedPerson {
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

export interface BaseExportedApiKey {
  label: string;
  service: string;
}

export interface BaseExportedHandle {
  nodeLabel: string;
  name: string;
  direction: 'input' | 'output';
  dataType: DataType;
  position?: HandlePosition;
  label?: string;
  maxConnections?: number;
}

export abstract class ConverterCore<TExportFormat = unknown> {
  // Label tracking for uniqueness
  protected usedNodeLabels = new Set<string>();
  protected usedPersonLabels = new Set<string>();
  protected usedApiKeyLabels = new Set<string>();
  
  // ID to label mappings for export
  protected nodeIdToLabel = new Map<NodeID, string>();
  protected personIdToLabel = new Map<PersonID, string>();
  protected apiKeyIdToLabel = new Map<ApiKeyID, string>();
  
  // Label to ID mappings for import
  protected nodeLabelToId = new Map<string, NodeID>();
  protected personLabelToId = new Map<string, PersonID>();
  protected apiKeyLabelToId = new Map<string, ApiKeyID>();

  /**
   * Reset all internal state - should be called before each conversion
   */
  protected reset(): void {
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

  /**
   * Ensure a label is unique by appending suffixes if needed
   */
  protected ensureUniqueLabel(label: string, usedLabels: Set<string>): string {
    if (!usedLabels.has(label)) {
      usedLabels.add(label);
      return label;
    }

    // Try numeric suffixes first (1-9)
    for (let i = 1; i <= 9; i++) {
      const candidate = `${label}_${i}`;
      if (!usedLabels.has(candidate)) {
        usedLabels.add(candidate);
        return candidate;
      }
    }

    // Then try alphabetic suffixes
    const alphabet = 'abcdefghijklmnopqrstuvwxyz';
    for (const letter of alphabet) {
      const candidate = `${label}-${letter}`;
      if (!usedLabels.has(candidate)) {
        usedLabels.add(candidate);
        return candidate;
      }
    }

    // Finally use a random suffix
    const candidate = `${label}_${generateShortId()}`;
    usedLabels.add(candidate);
    return candidate;
  }

  /**
   * Convert a domain node to base exported format
   */
  protected convertNodeToBase(node: DomainNode): BaseExportedNode {
    const label = this.ensureUniqueLabel(
      String(node.data.label || node.type || 'node'),
      this.usedNodeLabels
    );
    
    this.nodeIdToLabel.set(node.id, label);
    
    return {
      label,
      type: node.type,
      position: { ...node.position },
      data: { ...node.data }
    };
  }

  /**
   * Convert a domain arrow to base exported format
   */
  protected convertArrowToBase(arrow: DomainArrow, _nodes: DomainNode[]): BaseExportedArrow | null {
    const { nodeId: sourceNodeId, handleName: sourceHandleName } = parseHandleId(arrow.source);
    const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);
    
    const sourceLabel = this.nodeIdToLabel.get(sourceNodeId);
    const targetLabel = this.nodeIdToLabel.get(targetNodeId);
    
    if (!sourceLabel || !targetLabel) {
      console.warn('Arrow references unknown node', { arrow, sourceLabel, targetLabel });
      return null;
    }
    
    return {
      sourceNode: sourceLabel,
      sourceHandle: sourceHandleName,
      targetNode: targetLabel,
      targetHandle: targetHandleName,
      ...(arrow.data && Object.keys(arrow.data).length > 0 && { data: arrow.data })
    };
  }

  /**
   * Convert a domain person to base exported format
   */
  protected convertPersonToBase(person: DomainPerson): BaseExportedPerson {
    const label = this.ensureUniqueLabel(
      person.label || 'person',
      this.usedPersonLabels
    );
    
    this.personIdToLabel.set(person.id, label);
    
    const result: BaseExportedPerson = {
      label,
      model: person.model,
      service: person.service,
    };

    // Add optional fields only if they exist and are not default values
    if (person.systemPrompt) result.systemPrompt = person.systemPrompt;
    if (person.temperature !== undefined && person.temperature !== 0.7) result.temperature = person.temperature;
    if (person.maxTokens !== undefined && person.maxTokens !== 4096) result.maxTokens = person.maxTokens;
    if (person.topP !== undefined && person.topP !== 1) result.topP = person.topP;
    if (person.frequencyPenalty !== undefined && person.frequencyPenalty !== 0) result.frequencyPenalty = person.frequencyPenalty;
    if (person.presencePenalty !== undefined && person.presencePenalty !== 0) result.presencePenalty = person.presencePenalty;
    
    // Handle API key reference
    if (person.apiKeyId) {
      const apiKeyLabel = this.apiKeyIdToLabel.get(person.apiKeyId);
      if (apiKeyLabel) {
        result.apiKeyLabel = apiKeyLabel;
      }
    }
    
    return result;
  }

  /**
   * Convert a domain API key to base exported format
   */
  protected convertApiKeyToBase(apiKey: DomainApiKey): BaseExportedApiKey {
    const label = this.ensureUniqueLabel(
      apiKey.name || 'api_key',
      this.usedApiKeyLabels
    );
    
    this.apiKeyIdToLabel.set(apiKey.id, label);
    
    return {
      label,
      service: apiKey.service
    };
  }

  /**
   * Convert a domain handle to base exported format
   */
  protected convertHandleToBase(handle: DomainHandle): BaseExportedHandle | null {
    const nodeLabel = this.nodeIdToLabel.get(handle.nodeId);
    if (!nodeLabel) {
      console.warn('Handle references unknown node', { handle });
      return null;
    }
    
    return {
      nodeLabel,
      name: handle.name,
      direction: handle.direction,
      dataType: handle.dataType,
      ...(handle.position && { position: handle.position }),
      ...(handle.label && { label: handle.label }),
      ...(handle.maxConnections !== undefined && { maxConnections: handle.maxConnections })
    };
  }

  /**
   * Find the next available ID for a given label and collection
   */
  protected findAvailableId<T extends { id: string }>(
    baseLabel: string,
    collection: T[],
    generateId: (label: string) => string
  ): string {
    const baseId = generateId(baseLabel);
    if (!collection.some(item => item.id === baseId)) {
      return baseId;
    }

    // Try with numeric suffixes
    for (let i = 1; i <= 100; i++) {
      const candidateId = generateId(`${baseLabel}_${i}`);
      if (!collection.some(item => item.id === candidateId)) {
        return candidateId;
      }
    }

    // Fall back to random ID
    return generateId(`${baseLabel}_${generateShortId()}`);
  }

  /**
   * Abstract methods that must be implemented by specific converters
   */
  abstract serialize(diagram: ConverterDiagram): string;
  abstract deserialize(content: string): ConverterDiagram;
}