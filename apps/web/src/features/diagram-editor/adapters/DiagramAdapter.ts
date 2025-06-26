/**
 * DiagramAdapter - React Flow Integration Layer
 * 
 * PURPOSE:
 * This adapter handles conversions between DiPeO's domain models and React Flow's
 * visual representation. It is specifically focused on the UI layer integration.
 * 
 * RESPONSIBILITIES:
 * - Convert domain nodes/arrows to React Flow nodes/edges
 * - Convert React Flow elements back to domain models
 * - Validate connections according to business rules
 * - Cache conversions for performance optimization
 * 
 * NOT RESPONSIBLE FOR:
 * - GraphQL type conversions (see @/graphql/types)
 * - Data structure conversions (Arrays <-> Maps)
 * - Domain model definitions
 * 
 * USAGE:
 * Import this adapter when working with React Flow components.
 * For data conversions, import from '@/graphql/types' instead.
 */

import { Node as RFNode, Edge as RFEdge, Connection, Node, Edge } from '@xyflow/react';
import { ArrowID, DomainArrow, DomainHandle, DomainNode, HandleID, NodeID, ReactDiagram, arrowId, nodeId, createHandleId, parseHandleId } from '@/core/types';

import { nodeKindToGraphQLType, graphQLTypeToNodeKind, areHandlesCompatible, getNodeHandles } from '@/graphql/types';
import { generateId } from '@/core/types/utilities';
import { HandleDirection } from '@dipeo/domain-models';

/**
 * React Flow specific diagram representation
 */
export interface ReactFlowDiagram {
  nodes: Node[];
  edges: Edge[];
}

/**
 * React node with DiPeO data
 */
export interface DiPeoNode extends Node {
  data: Record<string, unknown> & {
    label: string;
    inputs?: Record<string, unknown>;
    outputs?: Record<string, unknown>;
  };
  draggable?: boolean;
  selectable?: boolean;
  connectable?: boolean;
  focusable?: boolean;
  deletable?: boolean;
}

/**
 * React edge with DiPeO data
 */
export interface DiPeoEdge extends Edge {
  data?: {
    label?: string;
    dataType?: string;
  };
}

/**
 * Extended connection with validation
 */
export interface ValidatedConnection extends Connection {
  isValid?: boolean;
  validationMessage?: string;
}

/**
 * React instance wrapper
 */
export interface DiPeoReactInstance {
  nodes: DiPeoNode[];
  edges: DiPeoEdge[];
  getNode: (id: string) => DiPeoNode | undefined;
  getEdge: (id: string) => DiPeoEdge | undefined;
  getNodes: () => DiPeoNode[];
  getEdges: () => DiPeoEdge[];
}

/**
 * Type guards
 */
export function isDiPeoNode(node: Node): node is DiPeoNode {
  return node && typeof node.data === 'object' && 'label' in node.data;
}

export function isDiPeoEdge(edge: Edge): edge is DiPeoEdge {
  return edge && typeof edge === 'object';
}

export class DiagramAdapter {
  // Cache for performance optimization
  private static nodeCache = new WeakMap<DomainNode, DiPeoNode>();
  private static edgeCache = new WeakMap<DomainArrow, DiPeoEdge>();
  private static reverseNodeCache = new WeakMap<RFNode, DomainNode>();
  private static reverseEdgeCache = new WeakMap<RFEdge, DomainArrow>();

  /**
   * Convert full domain diagram to React Flow format
   */
  static toReactFlow(diagram: ReactDiagram): {
    nodes: DiPeoNode[];
    edges: DiPeoEdge[];
  } {
    const nodes = (diagram.nodes || []).map((node: DomainNode) => {
      const handles = getNodeHandles(diagram, node.id as NodeID);
      return this.nodeToReactFlow(node, handles);
    });

    const edges = (diagram.arrows || []).map((arrow: DomainArrow) => 
      this.arrowToReactFlow(arrow)
    );

    return { nodes, edges };
  }

  /**
   * Convert domain node to React Flow node with caching
   */
  static nodeToReactFlow(node: DomainNode, handles: DomainHandle[]): DiPeoNode {
    // Check cache first
    const cached = this.nodeCache.get(node);
    if (cached && this.handlesMatch(cached, handles)) {
      return cached;
    }

    // Generate handles map
    const inputs = handles
      .filter(h => h.direction === HandleDirection.INPUT)
      .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});
    
    const outputs = handles
      .filter(h => h.direction === HandleDirection.OUTPUT)
      .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});

    const reactNode: DiPeoNode = {
      id: node.id,
      type: graphQLTypeToNodeKind(node.type),
      position: { ...node.position }, // Clone to prevent mutations
      data: {
        ...(node.data || {}), // Spread all existing node data first
        label: ((node.data as Record<string, unknown>)?.label as string) || node.displayName || '', // Use label from data or displayName as fallback
        inputs,
        outputs,
        _handles: handles // Store original handles for reference
      },
      // React Flow defaults
      draggable: true,
      selectable: true,
      connectable: true,
      focusable: true,
      deletable: true
    };

    // Cache the result
    this.nodeCache.set(node, reactNode);
    return reactNode;
  }

  /**
   * Convert domain arrow to React Flow edge with caching
   */
  static arrowToReactFlow(arrow: DomainArrow): DiPeoEdge {
    // Check cache first
    const cached = this.edgeCache.get(arrow);
    if (cached) {
      return cached;
    }

    const { nodeId: sourceNode, handleName: sourceHandle } = parseHandleId(arrow.source as HandleID);
    const { nodeId: targetNode, handleName: targetHandle } = parseHandleId(arrow.target as HandleID);
    
    const reactEdge: DiPeoEdge = {
      id: arrow.id,
      type: 'customArrow',
      source: sourceNode,
      target: targetNode,
      sourceHandle,
      targetHandle,
      data: arrow.data || {},
      animated: false,
      deletable: true,
      focusable: true,
      selectable: true
    };

    // Cache the result
    this.edgeCache.set(arrow, reactEdge);
    return reactEdge;
  }

  /**
   * Convert React Flow node back to domain node
   */
  static reactToNode(rfNode: RFNode): DomainNode {
    // Check reverse cache
    const cached = this.reverseNodeCache.get(rfNode);
    if (cached) {
      return cached;
    }

    const { _handles, ...nodeData } = rfNode.data || {};
    
    const domainNode: DomainNode = {
      id: rfNode.id as NodeID,
      type: nodeKindToGraphQLType(rfNode.type || 'start'),
      position: { ...rfNode.position },
      data: nodeData as Record<string, unknown>,
      displayName: (nodeData.label || rfNode.id) as string,
      handles: Array.isArray(_handles) ? _handles : []
    };

    // Cache the result
    this.reverseNodeCache.set(rfNode, domainNode);
    return domainNode;
  }

  /**
   * Convert React Flow edge back to domain arrow
   */
  static reactToArrow(rfEdge: RFEdge): DomainArrow {
    // Check reverse cache
    const cached = this.reverseEdgeCache.get(rfEdge);
    if (cached) {
      return cached;
    }

    const sourceHandle = createHandleId(
      rfEdge.source as NodeID, 
      rfEdge.sourceHandle || 'default'
    );
    const targetHandle = createHandleId(
      rfEdge.target as NodeID,
      rfEdge.targetHandle || 'default'
    );

    const domainArrow: DomainArrow = {
      id: rfEdge.id as ArrowID,
      source: sourceHandle,
      target: targetHandle,
      data: rfEdge.data || {}
    };

    // Cache the result
    this.reverseEdgeCache.set(rfEdge, domainArrow);
    return domainArrow;
  }

  /**
   * Convert React Flow connection to domain arrow
   */
  static connectionToArrow(connection: Connection): DomainArrow | null {
    if (!connection.source || !connection.target) {
      return null;
    }

    const sourceHandle = createHandleId(
      connection.source as NodeID,
      connection.sourceHandle || 'default'
    );
    const targetHandle = createHandleId(
      connection.target as NodeID,
      connection.targetHandle || 'default'
    );

    return {
      id: generateId() as ArrowID,
      source: sourceHandle,
      target: targetHandle,
      data: {}
    };
  }

  /**
   * Validate a connection against diagram rules
   */
  static validateConnection(
    connection: Connection,
    diagram: ReactDiagram
  ): ValidatedConnection {
    const validated: ValidatedConnection = { ...connection };

    if (!connection.source || !connection.target) {
      validated.isValid = false;
      validated.validationMessage = 'Missing source or target';
      return validated;
    }

    // Self-connections not allowed
    if (connection.source === connection.target) {
      validated.isValid = false;
      validated.validationMessage = 'Cannot connect node to itself';
      return validated;
    }

    const sourceHandleId = createHandleId(
      connection.source as NodeID,
      connection.sourceHandle || 'default'
    );
    const targetHandleId = createHandleId(
      connection.target as NodeID,
      connection.targetHandle || 'default'
    );

    // Find the actual handles
    const sourceNode = diagram.nodes.find((n: DomainNode) => n.id === connection.source);
    const targetNode = diagram.nodes.find((n: DomainNode) => n.id === connection.target);
    
    if (!sourceNode || !targetNode) {
      validated.isValid = false;
      validated.validationMessage = 'Node not found';
      return validated;
    }

    const sourceHandles = getNodeHandles(diagram, nodeId(connection.source));
    const targetHandles = getNodeHandles(diagram, nodeId(connection.target));

    const sourceHandle = sourceHandles.find((h: DomainHandle) => 
      h.label === (connection.sourceHandle || 'default')
    );
    const targetHandle = targetHandles.find((h: DomainHandle) => 
      h.label === (connection.targetHandle || 'default')
    );

    if (!sourceHandle || !targetHandle) {
      validated.isValid = false;
      validated.validationMessage = 'Handle not found';
      return validated;
    }

    // Check compatibility
    if (!areHandlesCompatible(sourceHandle, targetHandle)) {
      validated.isValid = false;
      validated.validationMessage = `Incompatible types: ${sourceHandle.dataType} → ${targetHandle.dataType}`;
      return validated;
    }

    // Check for duplicate connections
    const existingArrow = Object.values(diagram.arrows).find((arrow: DomainArrow) =>
      arrow.source === sourceHandleId && arrow.target === targetHandleId
    );
    
    if (existingArrow) {
      validated.isValid = false;
      validated.validationMessage = 'Connection already exists';
      return validated;
    }

    validated.isValid = true;
    return validated;
  }

  /**
   * Generate handles for a node based on its type
   */
  static generateHandles(_node: DomainNode): DomainHandle[] {
    // This would be implemented based on node type configurations
    // For now, returning empty array as handles are provided separately
    return [];
  }

  /**
   * Clear all caches (useful for memory management)
   */
  static clearCaches(): void {
    this.nodeCache = new WeakMap();
    this.edgeCache = new WeakMap();
    this.reverseNodeCache = new WeakMap();
    this.reverseEdgeCache = new WeakMap();
  }

  /**
   * Helper to check if handles match cached version
   */
  private static handlesMatch(cachedNode: DiPeoNode, handles: DomainHandle[]): boolean {
    const cachedHandles = cachedNode.data._handles;
    if (!cachedHandles || !Array.isArray(cachedHandles) || cachedHandles.length !== handles.length) {
      return false;
    }
    
    return handles.every((h, i) => {
      const cachedHandle = (cachedHandles as DomainHandle[])[i];
      return cachedHandle && 
        h.id === cachedHandle.id &&
        h.label === cachedHandle.label &&
        h.direction === cachedHandle.direction;
    });
  }

  /**
   * Convert array of React Flow nodes to domain nodes
   */
  static reactNodesToDomain(rfNodes: RFNode[]): Map<NodeID, DomainNode> {
    const nodes = new Map<NodeID, DomainNode>();
    rfNodes.forEach(rfNode => {
      const domainNode = this.reactToNode(rfNode);
      nodes.set(nodeId(domainNode.id), domainNode);
    });
    return nodes;
  }

  /**
   * Convert array of React Flow edges to domain arrows
   */
  static reactEdgesToDomain(rfEdges: RFEdge[]): Map<ArrowID, DomainArrow> {
    const arrows = new Map<ArrowID, DomainArrow>();
    rfEdges.forEach(rfEdge => {
      const domainArrow = this.reactToArrow(rfEdge);
      arrows.set(arrowId(domainArrow.id), domainArrow);
    });
    return arrows;
  }
}

// Static function exports for backward compatibility with existing code
export const nodeToReact = (node: DomainNode, handles: DomainHandle[]) => 
  DiagramAdapter.nodeToReactFlow(node, handles);

export const arrowToReact = (arrow: DomainArrow) => 
  DiagramAdapter.arrowToReactFlow(arrow);

export const diagramToReact = (diagram: ReactDiagram) => 
  DiagramAdapter.toReactFlow(diagram);

export const reactToNode = (rfNode: RFNode) => 
  DiagramAdapter.reactToNode(rfNode);

export const reactToArrow = (rfEdge: RFEdge) => 
  DiagramAdapter.reactToArrow(rfEdge);

export const connectionToArrow = (connection: Connection) => 
  DiagramAdapter.connectionToArrow(connection);

export const validateConnection = (connection: Connection, diagram: ReactDiagram) => 
  DiagramAdapter.validateConnection(connection, diagram);

// Note: Import data conversion functions directly from '@/graphql/types' when needed
// This adapter focuses solely on React Flow conversions
