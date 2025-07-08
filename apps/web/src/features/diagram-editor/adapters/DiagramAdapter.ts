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
 * - GraphQL type conversions (see @/lib/graphql/types)
 * - Data structure conversions (Arrays <-> Maps)
 * - Domain model definitions
 * 
 * USAGE:
 * Import this adapter when working with React Flow components.
 * For data conversions, import from '@/lib/graphql/types' instead.
 */

import { Node as RFNode, Edge as RFEdge, Connection, Node, Edge } from '@xyflow/react';
import { ArrowID, DomainArrow, DomainHandle, DomainNode, HandleID, NodeID, DomainDiagramType, arrowId, nodeId } from '@/core/types';

import { nodeKindToGraphQLType, graphQLTypeToNodeKind, areHandlesCompatible } from '@/lib/graphql/types';
import { generateId } from '@/core/types/utilities';
import { HandleDirection, HandleLabel, createHandleId, parseHandleId } from '@dipeo/domain-models';
import { ContentType } from '@/__generated__/graphql';
import { createHandleIndex, getHandlesForNode, findHandleByLabel } from '../utils/handleIndex';
import { ConversionService } from '@/core/services/ConversionService';

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

  /**
   * Convert full domain diagram to React Flow format
   */
  static toReactFlow(diagram: DomainDiagramType): {
    nodes: DiPeoNode[];
    edges: DiPeoEdge[];
  } {
    const startTime = performance.now();
    
    // Pre-index handles for O(1) lookups
    const handleIndex = createHandleIndex(diagram.handles || []);
    const indexTime = performance.now();
    
    const nodes = (diagram.nodes || []).map((node: DomainNode) => {
      // O(1) lookup instead of O(n) filtering
      const handles = getHandlesForNode(handleIndex, node.id);
      return this.nodeToReactFlow(node, handles);
    });
    
    const nodesTime = performance.now();

    const edges = (diagram.arrows || []).map((arrow: DomainArrow) => 
      this.arrowToReactFlow(arrow)
    );
    
    const endTime = performance.now();
    
    // Log performance metrics in development
    if (import.meta.env.DEV && diagram.nodes.length > 10) {
      console.log('[Performance] DiagramAdapter.toReactFlow:', {
        totalTime: `${(endTime - startTime).toFixed(2)}ms`,
        indexingTime: `${(indexTime - startTime).toFixed(2)}ms`,
        nodeConversionTime: `${(nodesTime - indexTime).toFixed(2)}ms`,
        edgeConversionTime: `${(endTime - nodesTime).toFixed(2)}ms`,
        nodeCount: diagram.nodes.length,
        handleCount: diagram.handles?.length || 0,
        edgeCount: diagram.arrows?.length || 0
      });
    }

    return { nodes, edges };
  }

  /**
   * Convert domain node to React Flow node
   */
  static nodeToReactFlow(node: DomainNode, handles: DomainHandle[]): DiPeoNode {
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

    // Process node data
    const nodeData = { ...(node.data || {}) };
    
    // Convert tools array to comma-separated string for person_job nodes
    if (node.type === 'person_job' && Array.isArray(nodeData.tools)) {
      nodeData.tools = ConversionService.toolsArrayToString(nodeData.tools);
    }

    return {
      id: node.id,
      type: graphQLTypeToNodeKind(node.type),
      position,
      data: {
        ...nodeData, // Spread processed node data
        label: (nodeData?.label as string) || '', // Use label from data
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
  }


  /**
   * Convert domain arrow to React Flow edge
   */
  static arrowToReactFlow(arrow: DomainArrow): DiPeoEdge {
    const sourceParsed = ConversionService.parseHandleId(arrow.source);
    const targetParsed = ConversionService.parseHandleId(arrow.target);
    const sourceNode = sourceParsed.node_id;
    const targetNode = targetParsed.node_id;
    
    // React Flow needs handle IDs to match what FlowHandle component generates
    // FlowHandle generates: nodeId_handleId_direction
    // Our stored format is already: nodeId_label_direction  
    const sourceHandle = arrow.source;
    const targetHandle = arrow.target;
    
    // Merge arrow's direct fields (content_type, label) into data
    const edgeData = { ...(arrow.data || {}) };
    if (arrow.content_type) {
      edgeData.content_type = arrow.content_type;
    }
    if (arrow.label) {
      edgeData.label = arrow.label;
    }
    
    return {
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
  }

  /**
   * Convert React Flow node back to domain node
   */
  static reactToNode(rfNode: RFNode): DomainNode {
    const { _handles, ...nodeData } = rfNode.data || {};
    
    return {
      id: ConversionService.toNodeId(rfNode.id),
      type: nodeKindToGraphQLType(rfNode.type || 'start'),
      position: { ...rfNode.position },
      data: {
        ...nodeData,
        label: (nodeData.label || rfNode.id) as string
      } as Record<string, unknown>
    };
  }

  /**
   * Convert React Flow edge back to domain arrow
   */
  static reactToArrow(rfEdge: RFEdge): DomainArrow {
    // Map handle strings to HandleLabel enum
    const sourceHandleLabel = (rfEdge.sourceHandle || 'default') as HandleLabel;
    const targetHandleLabel = (rfEdge.targetHandle || 'default') as HandleLabel;
    
    const sourceHandle = ConversionService.createHandleId(
      ConversionService.toNodeId(rfEdge.source), 
      sourceHandleLabel,
      HandleDirection.OUTPUT
    );
    const targetHandle = ConversionService.createHandleId(
      ConversionService.toNodeId(rfEdge.target),
      targetHandleLabel,
      HandleDirection.INPUT
    );

    // Extract content_type and label from data
    const { content_type, label, ...restData } = rfEdge.data || {};
    
    const domainArrow: DomainArrow = {
      id: ConversionService.toArrowId(rfEdge.id),
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

    return domainArrow;
  }

  /**
   * Convert React Flow connection to domain arrow
   */
  static connectionToArrow(connection: Connection): DomainArrow | null {
    if (!connection.source || !connection.target) {
      return null;
    }

    const sourceHandleLabel = (connection.sourceHandle || 'default') as HandleLabel;
    const targetHandleLabel = (connection.targetHandle || 'default') as HandleLabel;
    
    const sourceHandle = ConversionService.createHandleId(
      ConversionService.toNodeId(connection.source),
      sourceHandleLabel,
      HandleDirection.OUTPUT
    );
    const targetHandle = ConversionService.createHandleId(
      ConversionService.toNodeId(connection.target),
      targetHandleLabel,
      HandleDirection.INPUT
    );

    return {
      id: ConversionService.toArrowId(generateId()),
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
    diagram: DomainDiagramType
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

    const sourceHandleLabel = (connection.sourceHandle || 'default') as HandleLabel;
    const targetHandleLabel = (connection.targetHandle || 'default') as HandleLabel;
    
    const sourceHandleId = ConversionService.createHandleId(
      ConversionService.toNodeId(connection.source),
      sourceHandleLabel,
      HandleDirection.OUTPUT
    );
    const targetHandleId = ConversionService.createHandleId(
      ConversionService.toNodeId(connection.target),
      targetHandleLabel,
      HandleDirection.INPUT
    );

    // Find the actual handles
    const sourceNode = diagram.nodes.find((n: DomainNode) => n.id === connection.source);
    const targetNode = diagram.nodes.find((n: DomainNode) => n.id === connection.target);
    
    if (!sourceNode || !targetNode) {
      validated.isValid = false;
      validated.validationMessage = 'Node not found';
      return validated;
    }

    // Pre-index handles for O(1) lookups
    const handleIndex = createHandleIndex(diagram.handles || []);
    
    const sourceHandle = findHandleByLabel(
      handleIndex,
      ConversionService.toNodeId(connection.source),
      connection.sourceHandle || 'default'
    );
    const targetHandle = findHandleByLabel(
      handleIndex,
      ConversionService.toNodeId(connection.target),
      connection.targetHandle || 'default'
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
   * Convert array of React Flow nodes to domain nodes
   */
  static reactNodesToDomain(rfNodes: RFNode[]): Map<NodeID, DomainNode> {
    const domainNodes = rfNodes.map(rfNode => this.reactToNode(rfNode));
    return ConversionService.arrayToMap(domainNodes, node => node.id);
  }

  /**
   * Convert array of React Flow edges to domain arrows
   */
  static reactEdgesToDomain(rfEdges: RFEdge[]): Map<ArrowID, DomainArrow> {
    const domainArrows = rfEdges.map(rfEdge => this.reactToArrow(rfEdge));
    return ConversionService.arrayToMap(domainArrows, arrow => arrow.id);
  }
}

// Note: Import data conversion functions directly from '@/lib/graphql/types' when needed
// This adapter focuses solely on React Flow conversions
