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
import { ArrowID, DomainArrow, DomainHandle, DomainNode, HandleID, NodeID, ReactDiagram, arrowId, nodeId } from '@/core/types';

import { nodeKindToGraphQLType, graphQLTypeToNodeKind, areHandlesCompatible, getNodeHandles } from '@/graphql/types';
import { generateId } from '@/core/types/utilities';
import { HandleDirection, createHandleId, parseHandleId } from '@dipeo/domain-models';
import { ContentType } from '@/__generated__/graphql';

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
    content_type?: ContentType | null;
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

    // Ensure position is always defined with valid numbers
    const position = node.position && 
                    typeof node.position.x === 'number' && 
                    typeof node.position.y === 'number' 
                    ? { x: node.position.x, y: node.position.y }
                    : { x: 0, y: 0 };

    const reactNode: DiPeoNode = {
      id: node.id,
      type: graphQLTypeToNodeKind(node.type),
      position,
      data: {
        ...(node.data || {}), // Spread all existing node data first
        label: ((node.data as Record<string, unknown>)?.label as string) || '', // Use label from data
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
   * Clear all caches - useful when loading new diagrams
   */
  static clearCaches() {
    // WeakMap doesn't have clear(), so reassign new instances
    this.nodeCache = new WeakMap<DomainNode, DiPeoNode>();
    this.edgeCache = new WeakMap<DomainArrow, DiPeoEdge>();
    this.reverseNodeCache = new WeakMap<RFNode, DomainNode>();
    this.reverseEdgeCache = new WeakMap<RFEdge, DomainArrow>();
  }

  /**
   * Convert domain arrow to React Flow edge with caching
   */
  static arrowToReactFlow(arrow: DomainArrow): DiPeoEdge {
    // Check cache first
    const cached = this.edgeCache.get(arrow);
    if (cached) {
      // Clear cache if arrow has been updated with label or content_type
      const cacheInvalid = 
        (arrow.label && cached.data?.label !== arrow.label) ||
        (arrow.content_type && cached.data?.content_type !== arrow.content_type) ||
        (!arrow.label && cached.data?.label) ||
        (!arrow.content_type && cached.data?.content_type);
        
      if (cacheInvalid) {
        this.edgeCache.delete(arrow);
      } else {
        return cached;
      }
    }

    const sourceParsed = parseHandleId(arrow.source as HandleID);
    const targetParsed = parseHandleId(arrow.target as HandleID);
    const sourceNode = sourceParsed.node_id;
    const sourceHandle = sourceParsed.handle_label;
    const targetNode = targetParsed.node_id;
    const targetHandle = targetParsed.handle_label;
    
    // Merge arrow's direct fields (content_type, label) into data
    const edgeData = { ...(arrow.data || {}) };
    if (arrow.content_type) {
      edgeData.content_type = arrow.content_type;
    }
    if (arrow.label) {
      edgeData.label = arrow.label;
      console.log(`DiagramAdapter: Arrow ${arrow.id} has label "${arrow.label}"`, edgeData);
    }
    
    const reactEdge: DiPeoEdge = {
      id: arrow.id,
      type: 'customArrow',
      source: sourceNode,
      target: targetNode,
      sourceHandle,
      targetHandle,
      data: edgeData,
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
      data: {
        ...nodeData,
        label: (nodeData.label || rfNode.id) as string
      } as Record<string, unknown>
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

    // Extract content_type and label from data
    const { content_type, label, ...restData } = rfEdge.data || {};
    
    const domainArrow: DomainArrow = {
      id: rfEdge.id as ArrowID,
      source: sourceHandle,
      target: targetHandle,
      data: Object.keys(restData).length > 0 ? restData : null
    };
    
    // Add content_type and label as direct fields if present
    if (content_type !== undefined && content_type !== null) {
      domainArrow.content_type = content_type as ContentType;
    }
    if (label !== undefined && label !== null && typeof label === 'string') {
      domainArrow.label = label;
    }

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
      validated.validationMessage = `Incompatible types: ${sourceHandle.data_type} → ${targetHandle.data_type}`;
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

// Note: Import data conversion functions directly from '@/graphql/types' when needed
// This adapter focuses solely on React Flow conversions
