import { DomainHandle, DataType, HandlePosition } from '@/types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import { YamlConverter } from '@/utils/converters';
import type { UnifiedStore, ExportFormat, ExportedHandle } from './unifiedStore.types';
import type { ConverterDiagram } from '@/utils/converters/types';

// Thin wrapper around YAML converter that provides store integration
export class DiagramExporter {
  private yamlConverter = new YamlConverter();
  
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
    const diagram = this.storeToDiagram();
    
    // Convert arrows to use handle references
    const arrows = diagram.arrows.map(arrow => {
      const sourceHandle = this.store.handles.get(arrow.source);
      const targetHandle = this.store.handles.get(arrow.target);
      
      if (!sourceHandle || !targetHandle) {
        throw new Error('Missing handle information for arrow');
      }
      
      const sourceNode = this.store.nodes.get(sourceHandle.nodeId);
      const targetNode = this.store.nodes.get(targetHandle.nodeId);
      
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
    const handles = Array.from(this.store.handles.values()).map(handle => {
      const node = this.store.nodes.get(handle.nodeId);
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
      nodes: diagram.nodes.map(node => ({
        label: (node.data.label as string) || node.id,
        type: node.type,
        position: { x: node.position.x, y: node.position.y },
        data: node.data
      })),
      handles,
      arrows,
      persons: diagram.persons.map(person => ({
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
      apiKeys: diagram.apiKeys.map(key => ({
        name: key.label,
        service: key.service
      })),
      metadata: {
        exported: new Date().toISOString()
      }
    };
  }

  exportAsYAML(): string {
    const diagram = this.storeToDiagram();
    return this.yamlConverter.serialize(diagram);
  }

  // Import operations
  importDiagram(data: ExportFormat | string): void {
    if (typeof data === 'string') {
      const diagram = this.yamlConverter.deserialize(data);
      this.diagramToStore(diagram);
    } else {
      // Convert from export format to ConverterDiagram
      const diagram = this.exportFormatToDiagram(data);
      this.diagramToStore(diagram);
    }
  }

  // Validation
  validateExportData(data: unknown): { valid: boolean; errors: string[] } {
    if (typeof data === 'string') {
      try {
        const diagram = this.yamlConverter.deserialize(data);
        return { valid: true, errors: [] };
      } catch (e) {
        return { valid: false, errors: [e instanceof Error ? e.message : 'Invalid YAML'] };
      }
    }
    
    // Basic validation for export format
    if (!data || typeof data !== 'object') {
      return { valid: false, errors: ['Data must be an object'] };
    }
    
    const exportData = data as any;
    const errors: string[] = [];
    
    if (!exportData.version) errors.push('Missing version');
    if (!Array.isArray(exportData.nodes)) errors.push('nodes must be an array');
    if (!Array.isArray(exportData.arrows)) errors.push('arrows must be an array');
    
    return { valid: errors.length === 0, errors };
  }

  // Private helper methods
  
  // Convert store state to diagram format for export
  private storeToDiagram(): ConverterDiagram {
    return {
      id: `diagram-${Date.now()}`,
      name: 'Exported Diagram',
      description: undefined,
      nodes: Array.from(this.store.nodes.values()),
      arrows: Array.from(this.store.arrows.values()),
      persons: Array.from(this.store.persons.values()),
      apiKeys: Array.from(this.store.apiKeys.values()),
      handles: Array.from(this.store.handles.values())
    };
  }
  
  // Convert diagram format to store state for import
  private diagramToStore(diagram: ConverterDiagram): void {
    // Clear existing data
    this.store.clearAll();
    
    // Import in transaction to ensure consistency
    this.store.transaction(() => {
      // Import API keys first
      diagram.apiKeys.forEach(apiKey => {
        this.store.apiKeys.set(apiKey.id, apiKey);
      });
      
      // Import persons
      diagram.persons.forEach(person => {
        this.store.persons.set(person.id, person);
      });
      
      // Import nodes
      diagram.nodes.forEach(node => {
        this.store.nodes.set(node.id, node);
      });
      
      // Import handles or generate them if missing
      if (diagram.handles && diagram.handles.length > 0) {
        diagram.handles.forEach(handle => {
          this.store.handles.set(handle.id, handle);
        });
      } else {
        // Generate handles for all nodes if not present
        this.regenerateHandlesForNodes();
      }
      
      // Import arrows
      diagram.arrows.forEach(arrow => {
        this.store.arrows.set(arrow.id, arrow);
      });
    });
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
  
  // Convert ExportFormat to ConverterDiagram
  private exportFormatToDiagram(data: ExportFormat): ConverterDiagram {
    // This is a simplified conversion - in a real implementation,
    // you'd need to properly reconstruct all the domain objects
    throw new Error('Direct ExportFormat import not implemented - use YAML string instead');
  }
}