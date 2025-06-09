import { createWithEqualityFn } from 'zustand/traditional';
import { devtools, persist } from 'zustand/middleware';
import { DiagramCanvasStore } from './diagramCanvasStore';
import {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey
} from '@/types/domain';
import {
  NodeID,
  ArrowID,
  PersonID,
  ApiKeyID,
  HandleID,
  nodeId,
  arrowId,
  personId,
  apiKeyId,
  handleId,
} from '@/types';
import { parseHandleId } from '@/types/domain/handle';
import { NodeKind, DataType, HandlePosition } from '@/types/primitives/enums';
import { generateShortId, generateArrowId } from '@/types/primitives/id-generation';
import { getNodeConfig } from '@/config/helpers';

// Export format types
interface ExportedNode {
  label: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
  handles?: Array<{
    name: string;
    direction: 'input' | 'output';
    dataType: string;
    position?: string;
    label?: string;
    maxConnections?: number;
  }>;
}

interface ExportedArrow {
  sourceLabel: string;
  targetLabel: string;
  sourceHandle: string;
  targetHandle: string;
  data?: Record<string, unknown>;
}

interface ExportedPerson {
  name: string;
  model: string;
  service: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  apiKeyLabel?: string;
}

interface ExportedApiKey {
  name: string;
  service: string;
}

interface ExportFormat {
  version: string;
  nodes: ExportedNode[];
  arrows: ExportedArrow[];
  persons: ExportedPerson[];
  apiKeys: ExportedApiKey[];
  metadata?: {
    exported: string;
    description?: string;
  };
}

// Optimized export class following DiagramCanvasStore patterns
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

  constructor(private domainStore: DiagramCanvasStore) {}

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
    const nodes = this.domainStore.getAllNodes();
    nodes.forEach(node => {
      const label = (node.data.label as string) || node.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedNodeLabels);
      this.nodeIdToLabel.set(node.id, uniqueLabel);
    });

    // Build person label mappings
    const persons = this.domainStore.getAllPersons();
    persons.forEach(person => {
      const label = person.name || person.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedPersonLabels);
      this.personIdToLabel.set(person.id, uniqueLabel);
    });

    // Build API key label mappings
    const apiKeys = this.domainStore.getAllApiKeys();
    apiKeys.forEach(apiKey => {
      const label = apiKey.name || apiKey.id;
      const uniqueLabel = this.ensureUniqueLabel(label, this.usedApiKeyLabels);
      this.apiKeyIdToLabel.set(apiKey.id, uniqueLabel);
    });
  }

  // Export operations
  exportDiagram(): ExportFormat {
    this.buildExportLookups();

    const nodes = this.domainStore.getAllNodes();
    const arrows = this.domainStore.getAllArrows();
    const persons = this.domainStore.getAllPersons();
    const apiKeys = this.domainStore.getAllApiKeys();

    // Export nodes with handles
    const exportedNodes = this.exportNodes(nodes);
    
    // Export arrows
    const exportedArrows = this.exportArrows(arrows);
    
    // Export persons
    const exportedPersons = this.exportPersons(persons);
    
    // Export API keys
    const exportedApiKeys = this.exportApiKeys(apiKeys);

    return {
      version: '3.0.0',
      nodes: exportedNodes,
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

    // Clear existing data
    this.domainStore.clear();
    this.clearLookups();

    // Import in order: API keys -> Persons -> Nodes -> Arrows
    this.importApiKeys(exportData.apiKeys);
    this.importPersons(exportData.persons);
    this.importNodes(exportData.nodes);
    this.importArrows(exportData.arrows);
  }

  // Validation
  validateExportData(data: unknown): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!data || typeof data !== 'object') {
      errors.push('Data must be an object');
      return { valid: false, errors };
    }

    const exportData = data as any;

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

    // Validate nodes
    if (Array.isArray(exportData.nodes)) {
      exportData.nodes.forEach((node: any, index: number) => {
        if (!node.label) errors.push(`Node ${index} missing label`);
        if (!node.type) errors.push(`Node ${index} missing type`);
        if (!node.position || typeof node.position.x !== 'number' || typeof node.position.y !== 'number') {
          errors.push(`Node ${index} missing valid position`);
        }
      });
    }

    // Validate arrows
    if (Array.isArray(exportData.arrows)) {
      exportData.arrows.forEach((arrow: any, index: number) => {
        if (!arrow.sourceLabel) errors.push(`Arrow ${index} missing sourceLabel`);
        if (!arrow.targetLabel) errors.push(`Arrow ${index} missing targetLabel`);
        if (!arrow.sourceHandle) errors.push(`Arrow ${index} missing sourceHandle`);
        if (!arrow.targetHandle) errors.push(`Arrow ${index} missing targetHandle`);
      });
    }

    return { valid: errors.length === 0, errors };
  }

  // Private export helpers
  private exportNodes(nodes: DomainNode[]): ExportedNode[] {
    return nodes.map(node => {
      const nodeHandles = this.domainStore.getNodeHandles(node.id);
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
        data,
        handles: nodeHandles.map(handle => ({
          name: handle.name,
          direction: handle.direction,
          dataType: handle.dataType,
          position: handle.position,
          label: handle.label,
          maxConnections: handle.maxConnections
        }))
      };
    });
  }

  private exportArrows(arrows: DomainArrow[]): ExportedArrow[] {
    return arrows.map(arrow => {
      const { nodeId: sourceNodeId, handleName: sourceHandleName } = parseHandleId(arrow.source);
      const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);

      const sourceLabel = this.nodeIdToLabel.get(sourceNodeId) || sourceNodeId;
      const targetLabel = this.nodeIdToLabel.get(targetNodeId) || targetNodeId;

      return {
        sourceLabel,
        targetLabel,
        sourceHandle: `${sourceLabel}-${sourceHandleName}`,
        targetHandle: `${targetLabel}-${targetHandleName}`,
        data: arrow.data
      };
    });
  }

  private exportPersons(persons: DomainPerson[]): ExportedPerson[] {
    return persons.map(person => {
      const result: ExportedPerson = {
        name: person.name,
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
      const id = apiKeyId(`APIKEY_${generateShortId().slice(0, 6).toUpperCase()}`);
      const label = this.ensureUniqueLabel(apiKeyData.name, this.usedApiKeyLabels);
      this.apiKeyLabelToId.set(label, id);

      this.domainStore.addApiKey({
        id,
        name: label,
        service: apiKeyData.service
      } as DomainApiKey);
    });
  }

  private importPersons(persons: ExportedPerson[]): void {
    persons.forEach(personData => {
      const id = personId(`person-${generateShortId().slice(0, 4)}`);
      const label = this.ensureUniqueLabel(personData.name, this.usedPersonLabels);
      this.personLabelToId.set(label, id);

      // Resolve API key reference
      const apiKeyId = personData.apiKeyLabel ? this.apiKeyLabelToId.get(personData.apiKeyLabel) : undefined;

      this.domainStore.addPerson({
        id,
        name: label,
        model: personData.model,
        service: personData.service,
        systemPrompt: personData.systemPrompt,
        temperature: personData.temperature,
        maxTokens: personData.maxTokens,
        ...(apiKeyId && { apiKeyId })
      } as DomainPerson);
    });
  }

  private importNodes(nodes: ExportedNode[]): void {
    nodes.forEach(nodeData => {
      const id = nodeId(`${nodeData.type}-${generateShortId().slice(0, 4)}`);
      const label = this.ensureUniqueLabel(nodeData.label, this.usedNodeLabels);
      this.nodeLabelToId.set(label, id);

      // Resolve person reference
      let resolvedPersonId: PersonID | undefined;
      if (nodeData.data.personLabel && this.personLabelToId.has(nodeData.data.personLabel as string)) {
        resolvedPersonId = this.personLabelToId.get(nodeData.data.personLabel as string);
        delete nodeData.data.personLabel;
      }

      // Create domain node
      const domainNode: DomainNode = {
        id,
        type: nodeData.type as NodeKind,
        position: nodeData.position,
        data: {
          ...nodeData.data,
          label,
          ...(resolvedPersonId && { personId: resolvedPersonId })
        }
      };

      this.domainStore.addNode(domainNode);

      // Add handles
      if (nodeData.handles) {
        nodeData.handles.forEach(handleData => {
          const handle: DomainHandle = {
            id: handleId(id, handleData.name),
            nodeId: id,
            name: handleData.name,
            direction: handleData.direction,
            dataType: handleData.dataType as DataType,
            position: handleData.position as HandlePosition,
            label: handleData.label,
            maxConnections: handleData.maxConnections
          };
          this.domainStore.addHandle(handle);
        });
      } else {
        // Generate default handles if not provided
        const nodeConfig = getNodeConfig(nodeData.type as NodeKind);
        if (nodeConfig?.handles) {
          const inputHandles = nodeConfig.handles.input || [];
          const outputHandles = nodeConfig.handles.output || [];
          
          [...inputHandles, ...outputHandles].forEach(handleData => {
            const handle: DomainHandle = {
              id: handleId(id, handleData.name),
              nodeId: id,
              name: handleData.name,
              direction: handleData.type === 'input' ? 'input' : 'output',
              dataType: handleData.dataType,
              position: handleData.position,
              label: handleData.label,
              maxConnections: handleData.maxConnections
            };
            this.domainStore.addHandle(handle);
          });
        }
      }
    });
  }

  private importArrows(arrows: ExportedArrow[]): void {
    arrows.forEach(arrowData => {
      // Resolve node IDs from labels
      const sourceNodeId = this.nodeLabelToId.get(arrowData.sourceLabel);
      const targetNodeId = this.nodeLabelToId.get(arrowData.targetLabel);

      if (!sourceNodeId || !targetNodeId) {
        console.warn(`Cannot resolve arrow nodes: ${arrowData.sourceLabel} -> ${arrowData.targetLabel}`);
        return;
      }

      // Extract handle names from compound labels
      const sourceHandleParts = arrowData.sourceHandle.split('-');
      const targetHandleParts = arrowData.targetHandle.split('-');

      // Remove the node label prefix to get handle name
      const sourceHandleName = sourceHandleParts.slice(1).join('-') || 'output';
      const targetHandleName = targetHandleParts.slice(1).join('-') || 'input';

      // Create handle IDs
      const sourceHandleId = handleId(sourceNodeId, sourceHandleName);
      const targetHandleId = handleId(targetNodeId, targetHandleName);

      // Verify handles exist
      if (!this.domainStore.getHandle(sourceHandleId) || !this.domainStore.getHandle(targetHandleId)) {
        console.warn(`Cannot find handles for arrow: ${sourceHandleId} -> ${targetHandleId}`);
        return;
      }

      // Create arrow
      const arrow: DomainArrow = {
        id: arrowId(generateArrowId()),
        source: sourceHandleId,
        target: targetHandleId,
        data: arrowData.data
      };

      this.domainStore.addArrow(arrow);
    });
  }

  // Utility methods
  private ensureUniqueLabel(label: string, existingLabels: Set<string>): string {
    if (!existingLabels.has(label)) {
      existingLabels.add(label);
      return label;
    }

    let counter = 2;
    while (existingLabels.has(`${label}_${counter}`)) {
      counter++;
    }
    const uniqueLabel = `${label}_${counter}`;
    existingLabels.add(uniqueLabel);
    return uniqueLabel;
  }

  private roundPosition(value: number): number {
    return Math.round(value * 10) / 10;
  }
}

interface DiagramExportStore {
  // Cached exporter instance
  exporter?: DiagramExporter;
  
  // Export operations
  exportDiagram: (domainStore: DiagramCanvasStore) => ExportFormat;
  exportAsJSON: (domainStore: DiagramCanvasStore) => string;

  // Import operations
  importDiagram: (data: ExportFormat | string, domainStore: DiagramCanvasStore) => void;

  // Validation
  validateExportData: (data: unknown) => { valid: boolean; errors: string[] };

  // Persistence
  lastExport?: ExportFormat;
  setLastExport: (data: ExportFormat) => void;
}

export const useDiagramExportStore = createWithEqualityFn<DiagramExportStore>()(
  devtools(
    persist(
      (set, get) => {
        let cachedExporter: DiagramExporter | undefined;

        return {
          lastExport: undefined,
          exporter: undefined,

          setLastExport: (data) => set({ lastExport: data }),

          exportDiagram: (domainStore) => {
            if (!cachedExporter || (cachedExporter as any).domainStore !== domainStore) {
              cachedExporter = new DiagramExporter(domainStore);
              (cachedExporter as any).domainStore = domainStore;
            }
            const exportData = cachedExporter.exportDiagram();
            set({ lastExport: exportData });
            return exportData;
          },

          exportAsJSON: (domainStore) => {
            if (!cachedExporter || (cachedExporter as any).domainStore !== domainStore) {
              cachedExporter = new DiagramExporter(domainStore);
              (cachedExporter as any).domainStore = domainStore;
            }
            return cachedExporter.exportAsJSON();
          },

          importDiagram: (data, domainStore) => {
            if (!cachedExporter || (cachedExporter as any).domainStore !== domainStore) {
              cachedExporter = new DiagramExporter(domainStore);
              (cachedExporter as any).domainStore = domainStore;
            }
            cachedExporter.importDiagram(data);
          },

          validateExportData: (data) => {
            // Use a static exporter instance for validation
            const tempExporter = new DiagramExporter({} as DiagramCanvasStore);
            return tempExporter.validateExportData(data);
          }
        };
      },
      {
        name: 'diagram-export-store-v3',
        partialize: (state) => ({ lastExport: state.lastExport })
      }
    ),
    {
      name: 'diagram-export-store'
    }
  )
);