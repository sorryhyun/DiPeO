import { 
  DomainHandle, 
  DomainNode,
  DomainArrow,
  DomainPerson,
  DomainApiKey,
  DomainDiagram,
  DataType, 
  HandlePosition,
  NodeKind,
  NodeID,
  ArrowID,
  PersonID,
  ApiKeyID,
  HandleID,
  generateNodeId,
  generateArrowId,
  generatePersonId,
  generateApiKeyId,
  createHandleId
} from '@/types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import type { UnifiedStore, ExportFormat } from './unifiedStore.types';
import { LightDomainConverter } from '@/utils/converters/formats/light-yaml';
import { storeDomainConverter } from '@/utils/converters/core';

// Thin wrapper around converters that provides store integration
export class DiagramExporter {
  private lightConverter = new LightDomainConverter();
  
  constructor(private store: UnifiedStore) {}
  
  // Parse handle reference - support both old "-" and new "::" separators
  private parseHandleRef(handleRef: string): { nodeLabel: string; handleLabel: string } {
    if (handleRef.includes('::')) {
      const parts = handleRef.split('::');
      return {
        nodeLabel: parts[0] || '',
        handleLabel: parts[1] || 'default'
      };
    }
    const lastHyphenIndex = handleRef.lastIndexOf('-');
    if (lastHyphenIndex === -1) {
      return {
        nodeLabel: handleRef,
        handleLabel: 'default'
      };
    }
    const nodeLabel = handleRef.substring(0, lastHyphenIndex);
    const handleLabel = handleRef.substring(lastHyphenIndex + 1) || 'default';
    return { nodeLabel, handleLabel };
  }

  // Export operations
  exportDiagram(): ExportFormat {
    const diagram = this.storeToDomainDiagram();
    
    // Convert arrows to use handle references
    const arrows = Object.values(diagram.arrows).map(arrow => {
      const sourceHandle = diagram.handles[arrow.source];
      const targetHandle = diagram.handles[arrow.target];
      
      if (!sourceHandle || !targetHandle) {
        throw new Error('Missing handle information for arrow');
      }
      
      const sourceNode = diagram.nodes[sourceHandle.nodeId];
      const targetNode = diagram.nodes[targetHandle.nodeId];
      
      if (!sourceNode || !targetNode) {
        throw new Error('Missing node information for arrow');
      }
      
      return {
        sourceHandle: `${(sourceNode.data.label as string) || sourceNode.id}::${sourceHandle.label}`,
        targetHandle: `${(targetNode.data.label as string) || targetNode.id}::${targetHandle.label}`,
        data: arrow.data
      };
    });
    
    // Convert handles to export format
    const handles = Object.values(diagram.handles).map(handle => {
      const node = diagram.nodes[handle.nodeId];
      const nodeLabel = (node?.data.label as string) || handle.nodeId;
      
      return {
        nodeLabel,
        label: handle.label,
        direction: handle.direction,
        dataType: handle.dataType as string,
        position: handle.position as string | undefined,
        maxConnections: handle.maxConnections
      };
    });
    
    // Convert to export format
    return {
      version: '1.0',
      nodes: Object.values(diagram.nodes).map(node => ({
        label: (node.data.label as string) || node.id,
        type: node.type,
        position: { x: node.position.x, y: node.position.y },
        data: node.data
      })),
      handles,
      arrows,
      persons: Object.values(diagram.persons).map(person => ({
        label: person.label,
        model: person.model,
        service: person.service,
        systemPrompt: person.systemPrompt,
        temperature: person.temperature,
        maxTokens: person.maxTokens,
        topP: person.topP,
        frequencyPenalty: person.frequencyPenalty,
        presencePenalty: person.presencePenalty
      })),
      apiKeys: Object.values(diagram.apiKeys).map(key => ({
        name: key.label,
        service: key.service
      })),
      metadata: {
        exported: new Date().toISOString()
      }
    };
  }

  exportAsYAML(): string {
    // Convert store state to domain model
    const storeState = {
      nodes: this.store.nodes,
      arrows: this.store.arrows,
      handles: this.store.handles,
      persons: this.store.persons,
      apiKeys: this.store.apiKeys
    };
    const domainDiagram = storeDomainConverter.storeToDomain(storeState);
    return this.lightConverter.serialize(domainDiagram);
  }

  // Import operations
  importDiagram(data: ExportFormat | string): void {
    if (typeof data === 'string') {
      // Handle YAML string import
      const domainDiagram = this.lightConverter.deserialize(data);
      const storeData = storeDomainConverter.domainToStore(domainDiagram);
      // Clear and import
      this.store.clearAll();
      this.store.transaction(() => {
        // Copy the new data into the store
        storeData.nodes.forEach((node, id) => this.store.nodes.set(id, node));
        storeData.arrows.forEach((arrow, id) => this.store.arrows.set(id, arrow));
        storeData.handles.forEach((handle, id) => this.store.handles.set(id, handle));
        storeData.persons.forEach((person, id) => this.store.persons.set(id, person));
        storeData.apiKeys.forEach((apiKey, id) => this.store.apiKeys.set(id, apiKey));
      });
    } else {
      // Handle ExportFormat import
      const domainDiagram = this.exportFormatToDomainDiagram(data);
      const storeData = storeDomainConverter.domainToStore(domainDiagram);
      // Clear and import
      this.store.clearAll();
      this.store.transaction(() => {
        // Copy the new data into the store
        storeData.nodes.forEach((node, id) => this.store.nodes.set(id, node));
        storeData.arrows.forEach((arrow, id) => this.store.arrows.set(id, arrow));
        storeData.handles.forEach((handle, id) => this.store.handles.set(id, handle));
        storeData.persons.forEach((person, id) => this.store.persons.set(id, person));
        storeData.apiKeys.forEach((apiKey, id) => this.store.apiKeys.set(id, apiKey));
      });
    }
  }

  // Validation
  validateExportData(data: unknown): { valid: boolean; errors: string[] } {
    if (typeof data === 'string') {
      try {
        this.lightConverter.deserialize(data);
        return { valid: true, errors: [] };
      } catch (e) {
        return { valid: false, errors: [e instanceof Error ? e.message : 'Invalid YAML'] };
      }
    }
    
    // Basic validation for export format
    if (!data || typeof data !== 'object') {
      return { valid: false, errors: ['Data must be an object'] };
    }
    
    const exportData = data as ExportFormat;
    const errors: string[] = [];
    
    if (!exportData.version) errors.push('Missing version');
    if (!Array.isArray(exportData.nodes)) errors.push('nodes must be an array');
    if (!Array.isArray(exportData.arrows)) errors.push('arrows must be an array');
    
    return { valid: errors.length === 0, errors };
  }

  // Private helper methods
  
  // Convert store state to domain diagram
  private storeToDomainDiagram(): DomainDiagram {
    const storeState = {
      nodes: this.store.nodes,
      arrows: this.store.arrows,
      handles: this.store.handles,
      persons: this.store.persons,
      apiKeys: this.store.apiKeys
    };
    return storeDomainConverter.storeToDomain(storeState);
  }
  
  // Convert ExportFormat to DomainDiagram
  private exportFormatToDomainDiagram(data: ExportFormat): DomainDiagram {
    // Generate unique IDs for all entities
    const nodeIdMap = new Map<string, NodeID>();
    const personIdMap = new Map<string, PersonID>();
    const apiKeyIdMap = new Map<string, ApiKeyID>();
    
    // Convert API keys first
    const apiKeys: Record<string, DomainApiKey> = {};
    (data.apiKeys || []).forEach(key => {
      const id = generateApiKeyId();
      apiKeyIdMap.set(key.name, id);
      apiKeys[id as string] = {
        id,
        label: key.name,
        service: key.service as DomainApiKey['service']
      };
    });
    
    // Convert persons
    const persons: Record<string, DomainPerson> = {};
    (data.persons || []).forEach(person => {
      const id = generatePersonId();
      personIdMap.set(person.label, id);
      persons[id as string] = {
        id,
        label: person.label,
        model: person.model,
        service: person.service as DomainPerson['service'],
        systemPrompt: person.systemPrompt,
        temperature: person.temperature,
        maxTokens: person.maxTokens,
        topP: person.topP,
        frequencyPenalty: person.frequencyPenalty,
        presencePenalty: person.presencePenalty
      };
    });
    
    // Convert nodes
    const nodes: Record<string, DomainNode> = {};
    (data.nodes || []).forEach(node => {
      const id = generateNodeId();
      nodeIdMap.set(node.label, id);
      
      // Update person references in node data
      const nodeData = { ...node.data };
      if (nodeData.personId && typeof nodeData.personId === 'string') {
        // Find the person by label and update to new ID
        const personLabel = (data.persons || []).find(p => p.label === nodeData.personId)?.label;
        if (personLabel && personIdMap.has(personLabel)) {
          nodeData.personId = personIdMap.get(personLabel);
        }
      }
      
      nodes[id as string] = {
        id,
        type: node.type as NodeKind,
        position: { x: node.position.x, y: node.position.y },
        data: nodeData
      };
    });
    
    // Convert handles
    const handles: Record<string, DomainHandle> = {};
    (data.handles || []).forEach(handle => {
      const nodeId = nodeIdMap.get(handle.nodeLabel);
      if (!nodeId) {
        throw new Error(`Handle references unknown node: ${handle.nodeLabel}`);
      }
      
      const id = createHandleId(nodeId, handle.label);
      handles[id as string] = {
        id,
        nodeId,
        label: handle.label,
        direction: handle.direction as 'input' | 'output',
        dataType: handle.dataType as DataType,
        position: handle.position as HandlePosition | undefined,
        maxConnections: handle.maxConnections
      };
    });
    
    // Generate default handles for nodes if not present
    if (data.handles.length === 0) {
      Object.values(nodes).forEach(node => {
        const nodeHandles = generateNodeHandlesFromRegistry(node.type, node.id);
        nodeHandles.forEach(handle => {
          handles[handle.id] = handle;
        });
      });
    }
    
    // Convert arrows
    const arrows: Record<string, DomainArrow> = {};
    (data.arrows || []).forEach(arrow => {
      // Parse the node label and handle label from the combined format
      const { nodeLabel: sourceNodeLabel, handleLabel: sourceHandleLabel } = this.parseHandleRef(arrow.sourceHandle);
      const { nodeLabel: targetNodeLabel, handleLabel: targetHandleLabel } = this.parseHandleRef(arrow.targetHandle);
      
      const sourceNodeId = nodeIdMap.get(sourceNodeLabel || '');
      const targetNodeId = nodeIdMap.get(targetNodeLabel || '');
      
      if (!sourceNodeId || !targetNodeId) {
        throw new Error(`Arrow references unknown nodes: ${sourceNodeLabel} -> ${targetNodeLabel}`);
      }
      
      const sourceHandleId = createHandleId(sourceNodeId, sourceHandleLabel || 'output');
      const targetHandleId = createHandleId(targetNodeId, targetHandleLabel || 'input');
      
      const id = generateArrowId();
      arrows[id as string] = {
        id,
        source: sourceHandleId,
        target: targetHandleId,
        data: arrow.data || {}
      };
    });
    
    return {
      nodes: nodes as Record<NodeID, DomainNode>,
      arrows: arrows as Record<ArrowID, DomainArrow>,
      handles: handles as Record<HandleID, DomainHandle>,
      persons: persons as Record<PersonID, DomainPerson>,
      apiKeys: apiKeys as Record<ApiKeyID, DomainApiKey>
    };
  }
}