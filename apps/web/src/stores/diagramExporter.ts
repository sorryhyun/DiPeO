import { DomainHandle, DataType, HandlePosition } from '@/types';
import { generateNodeHandlesFromRegistry } from '@/utils/node/handle-builder';
import { 
  toJSON, 
  fromJSON, 
  toExportFormat, 
  fromExportFormat, 
  validateExportData,
  type ExportFormat as JsonExportFormat,
  type ExportedHandle as JsonExportedHandle 
} from '@/utils/converters';
import type { UnifiedStore, ExportFormat, ExportedHandle } from './unifiedStore.types';
import type { ConverterDiagram } from '@/utils/converters/types';

// Thin wrapper around JSON converter that provides store integration
export class DiagramExporter {
  constructor(private store: UnifiedStore) {}
  
  // Parse handle reference - support both old "-" and new "::" separators
  private parseHandleRef(handleRef: string): { nodeLabel: string; handleName: string } {
    if (handleRef.includes('::')) {
      const parts = handleRef.split('::');
      return {
        nodeLabel: parts[0] || '',
        handleName: parts[1] || 'default'
      };
    }
    const lastHyphenIndex = handleRef.lastIndexOf('-');
    if (lastHyphenIndex === -1) {
      return {
        nodeLabel: handleRef,
        handleName: 'default'
      };
    }
    const nodeLabel = handleRef.substring(0, lastHyphenIndex);
    const handleName = handleRef.substring(lastHyphenIndex + 1) || 'default';
    return { nodeLabel, handleName };
  }

  // Export operations
  exportDiagram(): ExportFormat {
    const diagram = this.storeToDiagram();
    const jsonFormat = toExportFormat(diagram);
    
    // Convert from JSON format to store format
    return {
      version: jsonFormat.version,
      nodes: jsonFormat.nodes,
      handles: (jsonFormat.handles || []).map(handle => this.convertHandleToStore(handle)),
      arrows: jsonFormat.arrows.map(arrow => ({
        sourceHandle: `${arrow.sourceNode}::${arrow.sourceHandle}`,
        targetHandle: `${arrow.targetNode}::${arrow.targetHandle}`,
        data: arrow.data
      })),
      persons: jsonFormat.persons,
      apiKeys: jsonFormat.apiKeys.map(key => ({
        name: key.label,
        service: key.service
      })),
      metadata: {
        exported: new Date().toISOString(),
        description: jsonFormat.description
      }
    };
  }

  exportAsJSON(): string {
    const diagram = this.storeToDiagram();
    return toJSON(diagram);
  }

  // Import operations
  importDiagram(data: ExportFormat | string): void {
    if (typeof data === 'string') {
      const diagram = fromJSON(data);
      this.diagramToStore(diagram);
    } else {
      // Convert from store format to JSON format
      const jsonFormat: JsonExportFormat = {
        version: data.version,
        name: 'Imported Diagram',
        description: data.metadata?.description,
        nodes: data.nodes,
        arrows: data.arrows.map(arrow => {
          const source = this.parseHandleRef(arrow.sourceHandle);
          const target = this.parseHandleRef(arrow.targetHandle);
          
          return {
            sourceNode: source.nodeLabel,
            sourceHandle: source.handleName,
            targetNode: target.nodeLabel,
            targetHandle: target.handleName,
            data: arrow.data
          };
        }),
        persons: data.persons,
        apiKeys: data.apiKeys.map(key => ({
          label: key.name,
          service: key.service
        })),
        handles: data.handles.map(handle => this.convertHandleToJson(handle))
      };
      
      const diagram = fromExportFormat(jsonFormat);
      this.diagramToStore(diagram);
    }
  }

  // Validation
  validateExportData(data: unknown): { valid: boolean; errors: string[] } {
    // Convert to JSON format for validation if needed
    if (data && typeof data === 'object' && 'nodes' in data) {
      const exportData = data as ExportFormat;
      const jsonFormat: JsonExportFormat = {
        version: exportData.version,
        name: 'Validation',
        nodes: exportData.nodes,
        arrows: exportData.arrows.map(arrow => {
          const source = this.parseHandleRef(arrow.sourceHandle);
          const target = this.parseHandleRef(arrow.targetHandle);
          
          return {
            sourceNode: source.nodeLabel,
            sourceHandle: source.handleName,
            targetNode: target.nodeLabel,
            targetHandle: target.handleName,
            data: arrow.data
          };
        }),
        persons: exportData.persons,
        apiKeys: exportData.apiKeys.map(key => ({
          label: key.name,
          service: key.service
        })),
        handles: exportData.handles.map(handle => this.convertHandleToJson(handle))
      };
      return validateExportData(jsonFormat);
    }
    return validateExportData(data);
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
  
  // Convert handle from JSON format to store format
  private convertHandleToStore(handle: JsonExportedHandle): ExportedHandle {
    const result: ExportedHandle = {
      nodeLabel: handle.nodeLabel,
      name: handle.name,
      direction: handle.direction,
      dataType: handle.dataType as string,
      position: handle.position as string | undefined,
      label: handle.label,
      maxConnections: handle.maxConnections
    };
    
    // Handle type-specific properties
    if (handle.direction === 'input') {
      const inputHandle = handle as JsonExportedHandle & { required?: boolean; defaultValue?: unknown };
      if ('required' in inputHandle) result.required = inputHandle.required;
      if ('defaultValue' in inputHandle) result.defaultValue = inputHandle.defaultValue;
    } else if (handle.direction === 'output') {
      const outputHandle = handle as JsonExportedHandle & { dynamic?: boolean };
      if ('dynamic' in outputHandle) result.dynamic = outputHandle.dynamic;
    }
    
    return result;
  }
  
  // Convert handle from store format to JSON format
  private convertHandleToJson(handle: ExportedHandle): JsonExportedHandle {
    const result: JsonExportedHandle = {
      nodeLabel: handle.nodeLabel,
      name: handle.name,
      direction: handle.direction,
      dataType: handle.dataType as DataType
    };
    
    // Add optional fields
    if (handle.position) result.position = handle.position as HandlePosition;
    if (handle.label) result.label = handle.label;
    if (handle.maxConnections !== undefined) result.maxConnections = handle.maxConnections;
    
    return result;
  }
}