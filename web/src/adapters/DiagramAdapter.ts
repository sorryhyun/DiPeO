/**
 * Centralized adapter for domain<->ReactFlow conversions
 * Provides efficient, cached conversions with type safety
 */

import { Node as RFNode, Edge as RFEdge, Connection } from '@xyflow/react';
import { 
  DomainNode, 
  DomainArrow, 
  DomainHandle, 
  DomainDiagram,
  NodeID,
  ArrowID,
  HandleID,
  NodeKind,
  generateId,
  handleId,
  nodeId,
  arrowId,
  parseHandleId,
  createHandleId,
  areHandlesCompatible,
  getNodeHandles
} from '@/types';
import { DiPeoNode, DiPeoEdge, ValidatedConnection } from '@/types/framework/reactUtils';

export class DiagramAdapter {
  // Cache for performance optimization
  private static nodeCache = new WeakMap<DomainNode, DiPeoNode>();
  private static edgeCache = new WeakMap<DomainArrow, DiPeoEdge>();
  private static reverseNodeCache = new WeakMap<RFNode, DomainNode>();
  private static reverseEdgeCache = new WeakMap<RFEdge, DomainArrow>();

  /**
   * Convert full domain diagram to React Flow format
   */
  static toReactFlow(diagram: DomainDiagram): {
    nodes: DiPeoNode[];
    edges: DiPeoEdge[];
  } {
    const nodes = Object.values(diagram.nodes).map(node => {
      const handles = getNodeHandles(diagram, node.id as NodeID);
      return this.nodeToReactFlow(node, handles);
    });

    const edges = Object.values(diagram.arrows).map(arrow => 
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
      .filter(h => h.direction === 'input')
      .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});
    
    const outputs = handles
      .filter(h => h.direction === 'output')
      .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});

    const reactNode: DiPeoNode = {
      id: node.id,
      type: node.type,
      position: { ...node.position }, // Clone to prevent mutations
      data: {
        ...node.data,
        label: (node.data as any).label || '',
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

    const { inputs, outputs, _handles, ...nodeData } = rfNode.data || {};
    
    const domainNode = {
      id: rfNode.id as NodeID,
      type: (rfNode.type as NodeKind) || 'start',
      position: { ...rfNode.position },
      data: nodeData as any,
      displayName: (nodeData.label || rfNode.id) as string
    } as DomainNode;

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
    diagram: DomainDiagram
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
    const sourceNode = diagram.nodes[connection.source as NodeID];
    const targetNode = diagram.nodes[connection.target as NodeID];
    
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
    const existingArrow = Object.values(diagram.arrows).find(arrow =>
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
  static generateHandles(node: DomainNode): DomainHandle[] {
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
    
    return handles.every((h, i) => 
      h.id === (cachedHandles as DomainHandle[])[i].id &&
      h.label === (cachedHandles as DomainHandle[])[i].label &&
      h.direction === (cachedHandles as DomainHandle[])[i].direction
    );
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