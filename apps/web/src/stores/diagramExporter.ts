import {
  DomainNode,  DomainArrow,  DomainPerson, DomainApiKey,  DomainHandle,  
  InputHandle, OutputHandle, NodeID, PersonID,  ApiKeyID,  handleId,  
  parseHandleId,  NodeKind, LLMService, generateNodeId, DataType, HandlePosition
} from '@/types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import type { UnifiedStore, ExportFormat, ExportedNode, ExportedArrow, ExportedPerson, ExportedApiKey, ExportedHandle } from './unifiedStore.types';

// Optimized export class
export class DiagramExporter {
  // Pre-computed lookups for efficient export/import
  private nodeIdToLabel: Map<NodeID, string> = new Map();
  private personIdToLabel: Map<PersonID, string> = new Map();
  private apiKeyIdToLabel: Map<ApiKeyID, string> = new Map();
  private nodeLabelToId: Map<string, NodeID> = new Map();
  private personLabelToId: Map<string, PersonID> = new Map();
  private apiKeyLabelToId: Map<string, ApiKeyID> = new Map();
  
  // Label uniqueness tracking
  private usedNodeLabels: Set<string> = new Set();
  private usedPersonLabels: Set<string> = new Set();
  private usedApiKeyLabels: Set<string> = new Set();

  constructor(private store: UnifiedStore) {}

  // Clear all lookups
  private clearLookups(): void {
    this.nodeIdToLabel.clear();
    this.personIdToLabel.clear();
    this.apiKeyIdToLabel.clear();
    this.nodeLabelToId.clear();
    this.personLabelToId.clear();
    this.apiKeyLabelToId.clear();
    this.usedNodeLabels.clear();
    this.usedPersonLabels.clear();
    this.usedApiKeyLabels.clear();
  }

  // Build export lookups
  private buildExportLookups(): void {
    this.clearLookups();

    // Build node label mappings
    const nodes = Array.from(this.store.nodes.values());
    nodes.forEach(node => {
      const label = (node.data.label as string) || node.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedNodeLabels);
      this.nodeIdToLabel.set(node.id, uniqueLabel);
    });

    // Build person label mappings
    const persons = Array.from(this.store.persons.values());
    persons.forEach(person => {
      const label = person.label || person.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedPersonLabels);
      this.personIdToLabel.set(person.id, uniqueLabel);
    });

    // Build API key label mappings
    const apiKeys = Array.from(this.store.apiKeys.values());
    apiKeys.forEach(apiKey => {
      const label = apiKey.name || apiKey.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedApiKeyLabels);
      this.apiKeyIdToLabel.set(apiKey.id, uniqueLabel);
    });
  }

  // Export operations
  exportDiagram(): ExportFormat {
    this.buildExportLookups();

    const nodes = Array.from(this.store.nodes.values());
    const handles = Array.from(this.store.handles.values());
    const arrows = Array.from(this.store.arrows.values());
    const persons = Array.from(this.store.persons.values());
    const apiKeys = Array.from(this.store.apiKeys.values());

    // Export nodes
    const exportedNodes = this.exportNodes(nodes);
    
    // Export handles separately
    const exportedHandles = this.exportHandles(handles);
    
    // Export arrows
    const exportedArrows = this.exportArrows(arrows);
    
    // Export persons
    const exportedPersons = this.exportPersons(persons);
    
    // Export API keys
    const exportedApiKeys = this.exportApiKeys(apiKeys);

    return {
      version: '4.0.0',
      nodes: exportedNodes,
      handles: exportedHandles,
      arrows: exportedArrows,
      persons: exportedPersons,
      apiKeys: exportedApiKeys,
      metadata: {
        exported: new Date().toISOString()
      }
    };
  }

  exportAsJSON(): string {
    const exportData = this.exportDiagram();
    return JSON.stringify(exportData, null, 2);
  }

  // Import operations
  importDiagram(data: ExportFormat | string): void {
    const exportData: ExportFormat = typeof data === 'string'
      ? JSON.parse(data)
      : data;

    // Validate
    const validation = this.validateExportData(exportData);
    if (!validation.valid) {
      throw new Error(`Invalid export data: ${validation.errors.join(', ')}`);
    }

    // Clear existing data without using transaction
    this.store.clearAll();
    this.clearLookups();

    // Import in order: API keys -> Persons -> Nodes -> Handles -> Arrows
    this.store.transaction(() => {
      this.importApiKeys(exportData.apiKeys);
      this.importPersons(exportData.persons);
      
      // For v4.0.0+, we'll import handles separately, so skip auto-generation
      const skipHandleGeneration = exportData.version >= '4.0.0' && !!exportData.handles && exportData.handles.length > 0;
      this.importNodes(exportData.nodes, skipHandleGeneration);
      
      // Import handles if present (v4.0.0+)
      if (exportData.handles && Array.isArray(exportData.handles) && exportData.handles.length > 0) {
        this.importHandles(exportData.handles);
      } else if (exportData.version >= '4.0.0') {
        // If v4.0.0+ but no handles, we need to generate them
        console.warn('No handles found in v4.0.0+ export, regenerating handles');
        this.regenerateHandlesForNodes();
      }
      
      this.importArrows(exportData.arrows);
    });
  }

  // Validation
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
        if (!arrow.sourceHandle) errors.push(`Arrow ${index} missing sourceHandle`);
        if (!arrow.targetHandle) errors.push(`Arrow ${index} missing targetHandle`);
      });
    }

    return { valid: errors.length === 0, errors };
  }

  // Private export helpers
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

  private exportHandles(handles: DomainHandle[]): ExportedHandle[] {
    return handles.map(handle => {
      const nodeLabel = this.nodeIdToLabel.get(handle.nodeId) || handle.nodeId;
      
      const exportedHandle: ExportedHandle = {
        nodeLabel,
        name: handle.name,
        direction: handle.direction,
        dataType: handle.dataType,
        position: handle.position,
        label: handle.label,
        maxConnections: handle.maxConnections
      };

      // Type-safe handling of optional properties
      if (handle.direction === 'input') {
        const inputHandle = handle as InputHandle;
        if ('required' in inputHandle) exportedHandle.required = inputHandle.required;
        if ('defaultValue' in inputHandle) exportedHandle.defaultValue = inputHandle.defaultValue;
      } else if (handle.direction === 'output') {
        const outputHandle = handle as OutputHandle;
        if ('dynamic' in outputHandle) exportedHandle.dynamic = outputHandle.dynamic;
      }

      return exportedHandle;
    });
  }

  private exportArrows(arrows: DomainArrow[]): ExportedArrow[] {
    return arrows.map(arrow => {
      const { nodeId: sourceNodeId, handleName: sourceHandleName } = parseHandleId(arrow.source);
      const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);

      const sourceLabel = this.nodeIdToLabel.get(sourceNodeId) || sourceNodeId;
      const targetLabel = this.nodeIdToLabel.get(targetNodeId) || targetNodeId;

      return {
        sourceHandle: `${sourceLabel}::${sourceHandleName}`,
        targetHandle: `${targetLabel}::${targetHandleName}`,
        data: arrow.data
      };
    });
  }

  private exportPersons(persons: DomainPerson[]): ExportedPerson[] {
    return persons.map(person => {
      // Get the unique label for this person
      const label = this.personIdToLabel.get(person.id) || person.label;
      
      const result: ExportedPerson = {
        label,
        model: person.model,
        service: person.service,
        systemPrompt: person.systemPrompt,
        temperature: person.temperature,
        maxTokens: person.maxTokens
      };

      // Add API key label if exists
      if ('apiKeyId' in person && person.apiKeyId) {
        const apiKeyLabel = this.apiKeyIdToLabel.get(person.apiKeyId as ApiKeyID);
        if (apiKeyLabel) {
          result.apiKeyLabel = apiKeyLabel;
        }
      }

      return result;
    });
  }

  private exportApiKeys(apiKeys: DomainApiKey[]): ExportedApiKey[] {
    return apiKeys.map(apiKey => ({
      name: apiKey.name,
      service: apiKey.service
    }));
  }

  // Private import helpers
  private importApiKeys(apiKeys: ExportedApiKey[]): void {
    apiKeys.forEach(apiKeyData => {
      const label = this.ensureUniqueLabel(apiKeyData.name, this.usedApiKeyLabels);
      const id = this.store.addApiKey(label, apiKeyData.service);
      this.apiKeyLabelToId.set(label, id);
    });
  }

  private importPersons(persons: ExportedPerson[]): void {
    persons.forEach(personData => {
      const label = this.ensureUniqueLabel(personData.label, this.usedPersonLabels);
      
      // Create person using store action
      const id = this.store.addPerson(label, personData.service as LLMService, personData.model);
      this.personLabelToId.set(label, id);

      // Update with additional properties
      const updateData: Record<string, unknown> = {};
      if (personData.systemPrompt !== undefined) updateData.systemPrompt = personData.systemPrompt;
      if (personData.temperature !== undefined) updateData.temperature = personData.temperature;
      if (personData.maxTokens !== undefined) updateData.maxTokens = personData.maxTokens;
      
      // Resolve API key reference
      if (personData.apiKeyLabel) {
        const apiKeyId = this.apiKeyLabelToId.get(personData.apiKeyLabel);
        if (apiKeyId) updateData.apiKeyId = apiKeyId;
      }

      if (Object.keys(updateData).length > 0) {
        this.store.updatePerson(id, updateData as Partial<DomainPerson>);
      }
    });
  }

  private importNodes(nodes: ExportedNode[], skipHandleGeneration = false): void {
    nodes.forEach(nodeData => {
      const label = this.ensureUniqueLabel(nodeData.label, this.usedNodeLabels);
      
      // Resolve person reference
      let resolvedPersonId: PersonID | undefined;
      const personLabel = nodeData.data.personLabel;
      if (personLabel && this.personLabelToId.has(personLabel as string)) {
        resolvedPersonId = this.personLabelToId.get(personLabel as string);
      }

      // Create a new data object without personLabel (if it exists)
      const { personLabel: _, ...dataWithoutPersonLabel } = nodeData.data;

      // Prepare initial data for node creation
      const initialData = {
        ...dataWithoutPersonLabel,
        label,
        ...(resolvedPersonId && { personId: resolvedPersonId })
      };

      // Create node using store action
      // For v4.0.0+, handles will be imported separately
      if (skipHandleGeneration) {
        // Directly add node without auto-generating handles
        const nodeId = generateNodeId();
        const node: DomainNode = {
          id: nodeId,
          type: nodeData.type as NodeKind,
          position: nodeData.position,
          data: initialData
        };
        this.store.nodes.set(nodeId, node);
        this.nodeLabelToId.set(label, nodeId);
      } else {
        // Use regular addNode which auto-generates handles
        const id = this.store.addNode(nodeData.type as NodeKind, nodeData.position, initialData);
        this.nodeLabelToId.set(label, id);
      }
    });
  }

  private importHandles(handles: ExportedHandle[]): void {
    handles.forEach(handleData => {
      // Resolve node ID from label
      const nodeId = this.nodeLabelToId.get(handleData.nodeLabel);
      if (!nodeId) {
        console.warn(`Cannot resolve node for handle: ${handleData.nodeLabel}:${handleData.name}`);
        return;
      }

      // Create handle ID
      const id = handleId(nodeId, handleData.name);
      
      // Create handle based on direction
      if (handleData.direction === 'input') {
        const handle: InputHandle = {
          id,
          nodeId,
          name: handleData.name,
          direction: 'input',
          dataType: handleData.dataType as DataType,
          position: handleData.position as HandlePosition | undefined,
          label: handleData.label,
          maxConnections: handleData.maxConnections,
          ...(handleData.required !== undefined && { required: handleData.required }),
          ...(handleData.defaultValue !== undefined && { defaultValue: handleData.defaultValue })
        };
        this.store.handles.set(id, handle);
      } else {
        const handle: OutputHandle = {
          id,
          nodeId,
          name: handleData.name,
          direction: 'output',
          dataType: handleData.dataType as DataType,
          position: handleData.position as HandlePosition | undefined,
          label: handleData.label,
          maxConnections: handleData.maxConnections,
          ...(handleData.dynamic !== undefined && { dynamic: handleData.dynamic })
        };
        this.store.handles.set(id, handle);
      }
    });
  }

  private importArrows(arrows: ExportedArrow[]): void {
    arrows.forEach(arrowData => {
      // Parse handle references - support both old "-" and new "::" separators
      const parseHandleRef = (handleRef: string): { nodeLabel: string; handleName: string } => {
        // First try new format with "::" separator
        if (handleRef.includes('::')) {
          const parts = handleRef.split('::');
          return {
            nodeLabel: parts[0] || '',
            handleName: parts[1] || 'default'
          };
        }
        
        // Fall back to old format with "-" separator
        // For backward compatibility, we need to handle cases where node labels contain hyphens
        const lastHyphenIndex = handleRef.lastIndexOf('-');
        
        if (lastHyphenIndex === -1) {
          // No hyphen found, assume default handle
          return {
            nodeLabel: handleRef,
            handleName: 'default'
          };
        }
        
        // Extract node label and handle name
        const nodeLabel = handleRef.substring(0, lastHyphenIndex);
        const handleName = handleRef.substring(lastHyphenIndex + 1) || 'default';
        
        return { nodeLabel, handleName };
      };

      // Parse source and target handle references
      const source = parseHandleRef(arrowData.sourceHandle);
      const target = parseHandleRef(arrowData.targetHandle);

      // Validate we have node labels
      if (!source.nodeLabel || !target.nodeLabel) {
        console.warn(`Invalid arrow handle format: ${arrowData.sourceHandle} -> ${arrowData.targetHandle}`);
        return;
      }

      // Resolve node IDs from labels
      const sourceNodeId = this.nodeLabelToId.get(source.nodeLabel);
      const targetNodeId = this.nodeLabelToId.get(target.nodeLabel);

      if (!sourceNodeId || !targetNodeId) {
        console.warn(`Cannot resolve arrow nodes: ${source.nodeLabel} -> ${target.nodeLabel}`);
        return;
      }

      // Create handle IDs (we know these are defined from the check above)
      const sourceHandleId = handleId(sourceNodeId!, source.handleName);
      const targetHandleId = handleId(targetNodeId!, target.handleName);

      // Verify handles exist
      const sourceHandle = this.store.handles.get(sourceHandleId);
      const targetHandle = this.store.handles.get(targetHandleId);
      
      if (!sourceHandle || !targetHandle) {
        console.warn(`Cannot find handles for arrow: ${sourceHandleId} -> ${targetHandleId}`);
        return;
      }

      // Create arrow using store action
      this.store.addArrow(sourceHandleId, targetHandleId, arrowData.data);
    });
  }

  // Utility methods
  private ensureUniqueLabel(label: string, existingLabels: Set<string>): string {
    if (!existingLabels.has(label)) {
      existingLabels.add(label);
      return label;
    }

    // Generate alphabetic suffixes like -ab, -ac, -ad, etc.
    const generateSuffix = (index: number): string => {
      let suffix = '';
      while (index >= 0) {
        suffix = String.fromCharCode(97 + (index % 26)) + suffix;
        index = Math.floor(index / 26) - 1;
      }
      return suffix;
    };

    let counter = 0;
    let uniqueLabel: string;
    do {
      const suffix = generateSuffix(counter);
      uniqueLabel = `${label}-${suffix}`;
      counter++;
    } while (existingLabels.has(uniqueLabel));
    
    existingLabels.add(uniqueLabel);
    return uniqueLabel;
  }

  private roundPosition(value: number): number {
    return Math.round(value * 10) / 10;
  }
  
  private regenerateHandlesForNodes(): void {
    // Generate handles for all nodes
    this.store.nodes.forEach((node) => {
      const handles = generateNodeHandlesFromRegistry(node.id, node.type);
      handles.forEach((handle: DomainHandle) => {
        this.store.handles.set(handle.id, handle);
      });
    });
  }
}