import {
  type DomainDiagram,
  type DomainNode,
  type DomainArrow,
  type DomainHandle,
  type NodeID,
  type ArrowID,
  type HandleID,
  type HandleDirection,
  type HandleLabel,
  createHandleId,
  createEmptyDiagram,
  NodeType,
  DataType
} from '@dipeo/models';
import { Converters } from '../converters';
import { NodeService } from './node-service';
import { ValidationService } from './validation-service';
import { generateId } from '@/infrastructure/types/utilities';

interface ImportResult {
  success: boolean;
  diagram?: DomainDiagram;
  errors: string[];
}

interface ConnectionCreationOptions {
  sourceNodeId: NodeID;
  sourceHandle: HandleLabel;
  targetNodeId: NodeID;
  targetHandle: HandleLabel;
  label?: string;
}

interface BatchOperationResult<T> {
  successful: T[];
  failed: Array<{ item: T; error: string }>;
}

/**
 * DiagramOperations - High-level operations for diagram manipulation
 * Provides import/export, connection management, and batch operations
 */
export class DiagramOperations {
  /**
   * Import a diagram from JSON with validation
   * @param jsonString - JSON string to parse
   * @returns Import result with diagram or errors
   */
  static async importDiagram(jsonString: string): Promise<ImportResult> {
    const errors: string[] = [];
    
    try {
      // Parse JSON
      const parsed = JSON.parse(jsonString);
      
      // Ensure it has the basic structure
      if (!parsed || typeof parsed !== 'object') {
        errors.push('Invalid diagram format: not an object');
        return { success: false, errors };
      }
      
      // Create diagram with defaults
      const diagram: DomainDiagram = {
        ...createEmptyDiagram(),
        ...parsed
      };
      
      // Validate the diagram
      const validationResult = ValidationService.validateDiagram(diagram);
      
      if (!validationResult.valid) {
        errors.push(...validationResult.generalErrors);
        errors.push(...validationResult.connectionErrors);
        
        // Add node errors
        for (const [nodeId, fieldErrors] of validationResult.nodeErrors) {
          for (const [field, messages] of Object.entries(fieldErrors)) {
            errors.push(`Node ${nodeId} - ${field}: ${messages.join(', ')}`);
          }
        }
        
        return { success: false, errors };
      }
      
      return { success: true, diagram, errors: [] };
      
    } catch (error) {
      errors.push(`Failed to parse diagram: ${error instanceof Error ? error.message : String(error)}`);
      return { success: false, errors };
    }
  }
  
  /**
   * Export a diagram to JSON string
   * @param diagram - Diagram to export
   * @param pretty - Whether to pretty-print the JSON
   * @returns JSON string
   */
  static exportDiagram(diagram: DomainDiagram, pretty: boolean = true): string {
    // Clean up any internal properties before export
    const exportable = {
      nodes: diagram.nodes,
      handles: diagram.handles,
      arrows: diagram.arrows,
      persons: diagram.persons,
      metadata: {
        ...diagram.metadata,
        exported: new Date().toISOString()
      }
    };
    
    return JSON.stringify(exportable, null, pretty ? 2 : 0);
  }
  
  /**
   * Create a connection between two nodes
   * @param diagram - Current diagram state
   * @param options - Connection creation options
   * @returns Updated diagram or error
   */
  static createConnection(
    diagram: DomainDiagram,
    options: ConnectionCreationOptions
  ): { diagram?: DomainDiagram; error?: string } {
    const { sourceNodeId, sourceHandle, targetNodeId, targetHandle, label } = options;
    
    // Get nodes
    const diagramMaps = Converters.diagramArraysToMaps(diagram);
    const sourceNode = diagramMaps.nodes.get(sourceNodeId);
    const targetNode = diagramMaps.nodes.get(targetNodeId);
    
    if (!sourceNode) {
      return { error: `Source node ${sourceNodeId} not found` };
    }
    
    if (!targetNode) {
      return { error: `Target node ${targetNodeId} not found` };
    }
    
    // Create handle IDs
    const sourceHandleId = createHandleId(sourceNodeId, sourceHandle, 'output' as HandleDirection);
    const targetHandleId = createHandleId(targetNodeId, targetHandle, 'input' as HandleDirection);
    
    // Get or create handles
    let sourceHandleObj = diagramMaps.handles.get(sourceHandleId);
    let targetHandleObj = diagramMaps.handles.get(targetHandleId);
    
    // Validate connection
    if (sourceHandleObj && targetHandleObj) {
      const validation = ValidationService.validateConnection(sourceHandleObj!, targetHandleObj!);
      if (!validation.valid) {
        return { error: validation.errors.join(', ') };
      }
    }
    
    // Create handles if they don't exist
    const newHandles: DomainHandle[] = [];
    
    if (!sourceHandleObj) {
      sourceHandleObj = {
        id: sourceHandleId,
        node_id: sourceNodeId,
        direction: 'output' as HandleDirection,
        label: sourceHandle,
        data_type: DataType.ANY,
        position: null
      };
      newHandles.push(sourceHandleObj);
    }
    
    if (!targetHandleObj) {
      targetHandleObj = {
        id: targetHandleId,
        node_id: targetNodeId,
        direction: 'input' as HandleDirection,
        label: targetHandle,
        data_type: DataType.ANY,
        position: null
      };
      newHandles.push(targetHandleObj);
    }
    
    // Create arrow
    const arrow: DomainArrow = {
      id: Converters.toArrowId(`arrow_${generateId()}`),
      source: sourceHandleId,
      target: targetHandleId,
      label: label || '',
      content_type: null
    };
    
    // Return updated diagram
    return {
      diagram: {
        ...diagram,
        handles: [...diagram.handles, ...newHandles],
        arrows: [...diagram.arrows, arrow]
      }
    };
  }
  
  /**
   * Delete a connection from the diagram
   * @param diagram - Current diagram state
   * @param arrowId - ID of the arrow to delete
   * @returns Updated diagram
   */
  static deleteConnection(diagram: DomainDiagram, arrowId: ArrowID): DomainDiagram {
    return {
      ...diagram,
      arrows: diagram.arrows.filter(a => a.id !== arrowId)
    };
  }
  
  /**
   * Batch create multiple nodes
   * @param diagram - Current diagram state
   * @param nodes - Nodes to create
   * @returns Batch operation result
   */
  static batchCreateNodes(
    diagram: DomainDiagram,
    nodes: Array<{ type: NodeType | string; position: { x: number; y: number }; data?: Record<string, unknown> }>
  ): BatchOperationResult<DomainNode> {
    const successful: DomainNode[] = [];
    const failed: Array<{ item: DomainNode; error: string }> = [];
    
    for (const nodeSpec of nodes) {
      const nodeId = Converters.toNodeId(`node_${generateId()}`);
      
      // Get defaults for node type
      const defaults = NodeService.getNodeDefaults(nodeSpec.type);
      
      const node: DomainNode = {
        id: nodeId,
        type: nodeSpec.type as NodeType,
        position: nodeSpec.position,
        data: { ...defaults, ...nodeSpec.data }
      };
      
      // Validate node data
      const validation = ValidationService.validateNodeData(node.type, node.data);
      
      if (validation.success) {
        successful.push(node);
      } else {
        failed.push({
          item: node,
          error: `Validation failed: ${validation.error?.message || 'Unknown error'}`
        });
      }
    }
    
    return { successful, failed };
  }
  
  /**
   * Get all connections for a specific node
   * @param diagram - Diagram to search
   * @param nodeId - Node ID to find connections for
   * @returns Object with incoming and outgoing arrows
   */
  static getNodeConnections(
    diagram: DomainDiagram,
    nodeId: NodeID
  ): { incoming: DomainArrow[]; outgoing: DomainArrow[] } {
    const incoming: DomainArrow[] = [];
    const outgoing: DomainArrow[] = [];
    
    for (const arrow of diagram.arrows) {
      const sourceInfo = Converters.parseHandleId(arrow.source);
      const targetInfo = Converters.parseHandleId(arrow.target);
      
      if (sourceInfo.node_id === nodeId) {
        outgoing.push(arrow);
      }
      
      if (targetInfo.node_id === nodeId) {
        incoming.push(arrow);
      }
    }
    
    return { incoming, outgoing };
  }
  
  /**
   * Clone a node with new ID and position
   * @param node - Node to clone
   * @param newPosition - New position for cloned node
   * @returns Cloned node
   */
  static cloneNode(node: DomainNode, newPosition: { x: number; y: number }): DomainNode {
    return {
      ...node,
      id: Converters.toNodeId(`node_${generateId()}`),
      position: newPosition,
      data: { ...node.data }
    };
  }
  
  /**
   * Find all nodes of a specific type
   * @param diagram - Diagram to search
   * @param type - Node type to find
   * @returns Array of matching nodes
   */
  static findNodesByType(diagram: DomainDiagram, type: NodeType | string): DomainNode[] {
    return diagram.nodes.filter(node => node.type === type);
  }
  
  /**
   * Calculate diagram bounds
   * @param diagram - Diagram to calculate bounds for
   * @returns Bounding box
   */
  static calculateDiagramBounds(diagram: DomainDiagram): {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
    width: number;
    height: number;
  } {
    if (diagram.nodes.length === 0) {
      return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
    }
    
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    
    for (const node of diagram.nodes) {
      minX = Math.min(minX, node.position.x);
      minY = Math.min(minY, node.position.y);
      maxX = Math.max(maxX, node.position.x);
      maxY = Math.max(maxY, node.position.y);
    }
    
    return {
      minX,
      minY,
      maxX,
      maxY,
      width: maxX - minX,
      height: maxY - minY
    };
  }
}