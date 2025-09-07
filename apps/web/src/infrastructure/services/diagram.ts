/**
 * Diagram domain service - contains all diagram business logic
 * Leverages @dipeo/models for type-safe operations
 */

/**
 * Generate a short UUID-like string (8 characters)
 */
function generateShortId(): string {
  return Math.random().toString(36).substring(2, 10);
}

import type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainDiagram,
  NodeID,
  ArrowID,
  HandleID,
  DiagramID,
} from '@dipeo/models';
import {
  NodeType,
  HandleDirection,
} from '@dipeo/models';
import {
  createHandleId,
  parseHandleId,
} from '@dipeo/models';
import { Converters } from '../converters';
import { ValidationService } from './validation';
import { GraphQLService } from '../api/graphql';

/**
 * Diagram business operations
 */
export class DiagramService {
  /**
   * Create a new node with proper initialization
   */
  static createNode(type: NodeType, position: { x: number; y: number }): DomainNode {
    const nodeId = `node_${generateShortId()}` as NodeID;

    // Get node specification from @dipeo/models
    const nodeSpec = this.getNodeSpecification(type);

    return {
      id: nodeId,
      type,
      position,
      data: this.getDefaultNodeData(type),
    };
  }

  /**
   * Create a connection between nodes
   */
  static createArrow(
    sourceNodeId: NodeID,
    sourceHandle: HandleID,
    targetNodeId: NodeID,
    targetHandle: HandleID,
  ): DomainArrow | null {
    // Validate connection is allowed
    if (!this.canConnect(sourceHandle, targetHandle)) {
      return null;
    }

    const arrowId = `arrow_${generateShortId()}` as ArrowID;

    return {
      id: arrowId,
      source: sourceHandle,
      target: targetHandle,
    };
  }

  /**
   * Validate if two handles can be connected
   */
  static canConnect(sourceHandle: HandleID, targetHandle: HandleID): boolean {
    const source = parseHandleId(sourceHandle);
    const target = parseHandleId(targetHandle);

    // Can't connect to same node
    if (source.node_id === target.node_id) {
      return false;
    }

    // Must be output to input
    if (source.direction !== HandleDirection.OUTPUT || target.direction !== HandleDirection.INPUT) {
      return false;
    }

    // Additional type compatibility checks could go here
    return true;
  }

  /**
   * Get default data for a node type
   */
  private static getDefaultNodeData(type: NodeType): any {
    // This would be generated from @dipeo/models specifications
    const defaults: Record<NodeType, any> = {
      [NodeType.START]: {},
      [NodeType.PERSON_JOB]: {
        first_only_prompt: '',
        max_iteration: 5,
        tools: [],
      },
      [NodeType.CODE_JOB]: {
        code: '',
        language: 'python',
      },
      [NodeType.CONDITION]: {
        conditions: [],
        default_output: null,
      },
      [NodeType.API_JOB]: {
        url: '',
        method: 'GET',
        headers: {},
        body: null,
      },
      [NodeType.ENDPOINT]: {
        path: '',
        method: 'GET',
      },
      [NodeType.DB]: {
        query: '',
        database: '',
      },
      [NodeType.USER_RESPONSE]: {
        prompt: '',
        timeout: 300,
      },
      [NodeType.PERSON_BATCH_JOB]: {
        person: null,
        batch_size: 1,
        mode: 'parallel',
      },
      [NodeType.HOOK]: {
        hook_type: 'before',
        target_node: '',
      },
      [NodeType.TEMPLATE_JOB]: {
        template: '',
        variables: {},
      },
      [NodeType.JSON_SCHEMA_VALIDATOR]: {
        schema: {},
      },
      [NodeType.TYPESCRIPT_AST]: {
        code: '',
        query: '',
      },
      [NodeType.SUB_DIAGRAM]: {
        diagram_id: '',
        variables: {},
      },
      [NodeType.INTEGRATED_API]: {
        integration_type: '',
        action: '',
        config: {},
      },
    } as const;

    return defaults[type] || {};
  }

  /**
   * Get node specification from registry
   */
  private static getNodeSpecification(type: NodeType): any {
    // Would import from @dipeo/models node specifications
    return {
      defaultWidth: 200,
      defaultHeight: 100,
    };
  }

  /**
   * Optimize diagram layout
   */
  static optimizeLayout(diagram: DomainDiagram): DomainDiagram {
    // Auto-layout algorithm - simplified version
    const optimized = { ...diagram };

    // TODO: Implement proper auto-layout algorithm
    optimized.nodes = diagram.nodes.map(node => ({
      ...node,
      position: {
        x: node.position.x,
        y: node.position.y,
      },
    }));

    return optimized;
  }

  /**
   * Validate diagram structure
   */
  static validateDiagram(diagram: DomainDiagram): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Must have at least one START node
    const startNodes = diagram.nodes.filter(n => n.type === NodeType.START);
    if (startNodes.length === 0) {
      errors.push('Diagram must have at least one START node');
    }

    // Check for orphaned nodes
    const connectedNodeIds = new Set<NodeID>();
    diagram.arrows.forEach(arrow => {
      const sourceNodeId = parseHandleId(arrow.source).node_id;
      const targetNodeId = parseHandleId(arrow.target).node_id;
      connectedNodeIds.add(sourceNodeId);
      connectedNodeIds.add(targetNodeId);
    });

    diagram.nodes.forEach(node => {
      if (node.type !== NodeType.START && !connectedNodeIds.has(node.id)) {
        errors.push(`Node ${node.id} is not connected to the diagram`);
      }
    });

    // Check for cycles
    if (this.hasCycles(diagram)) {
      errors.push('Diagram contains cycles');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Check if diagram has cycles
   */
  private static hasCycles(diagram: DomainDiagram): boolean {
    // Simple cycle detection using DFS
    const visited = new Set<NodeID>();
    const recursionStack = new Set<NodeID>();

    const adjacencyList = new Map<NodeID, NodeID[]>();
    diagram.arrows.forEach(arrow => {
      const sourceNodeId = parseHandleId(arrow.source).node_id;
      const targetNodeId = parseHandleId(arrow.target).node_id;
      if (!adjacencyList.has(sourceNodeId)) {
        adjacencyList.set(sourceNodeId, []);
      }
      adjacencyList.get(sourceNodeId)!.push(targetNodeId);
    });

    const hasCycleDFS = (nodeId: NodeID): boolean => {
      visited.add(nodeId);
      recursionStack.add(nodeId);

      const neighbors = adjacencyList.get(nodeId) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          if (hasCycleDFS(neighbor)) {
            return true;
          }
        } else if (recursionStack.has(neighbor)) {
          return true;
        }
      }

      recursionStack.delete(nodeId);
      return false;
    };

    for (const node of diagram.nodes) {
      if (!visited.has(node.id)) {
        if (hasCycleDFS(node.id)) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Clone a diagram with new IDs
   */
  static cloneDiagram(diagram: DomainDiagram): DomainDiagram {
    const idMap = new Map<NodeID, NodeID>();
    const handleMap = new Map<HandleID, HandleID>();

    // Clone nodes with new IDs
    const clonedNodes = diagram.nodes.map(node => {
      const newId = `node_${generateShortId()}` as NodeID;
      idMap.set(node.id, newId);

      return {
        ...node,
        id: newId,
        data: { ...node.data },
      };
    });

    // Update handle IDs
    diagram.handles.forEach(handle => {
      const parsed = parseHandleId(handle.id);
      const newNodeId = idMap.get(parsed.node_id as NodeID);
      if (newNodeId) {
        const newHandleId = createHandleId(newNodeId, parsed.handle_label, parsed.direction);
        handleMap.set(handle.id, newHandleId);
      }
    });

    // Clone arrows with updated references
    const clonedArrows = diagram.arrows.map(arrow => ({
      ...arrow,
      id: `arrow_${generateShortId()}` as ArrowID,
      source: handleMap.get(arrow.source) || arrow.source,
      target: handleMap.get(arrow.target) || arrow.target,
    }));

    // Clone handles with updated IDs
    const clonedHandles = Array.from(diagram.handles).map(handle => ({
      ...handle,
      id: handleMap.get(handle.id) || handle.id,
    }));

    return {
      ...diagram,
      nodes: clonedNodes,
      arrows: clonedArrows,
      handles: clonedHandles,
      metadata: {
        ...diagram.metadata,
        id: `diagram_${generateShortId()}` as DiagramID,
        name: diagram.metadata?.name ? `${diagram.metadata.name} (Copy)` : 'Untitled (Copy)',
        version: diagram.metadata?.version || '1.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
      },
    };
  }

  /**
   * Export diagram to JSON
   */
  static exportToJSON(diagram: DomainDiagram): string {
    return JSON.stringify(diagram, null, 2);
  }

  /**
   * Import diagram from JSON
   */
  static importFromJSON(json: string): DomainDiagram {
    const parsed = JSON.parse(json);
    const diagram = parsed as DomainDiagram;

    // Validate imported diagram
    const validation = this.validateDiagram(diagram);
    if (!validation.valid) {
      throw new Error(`Invalid diagram: ${validation.errors.join(', ')}`);
    }

    return diagram;
  }
}
