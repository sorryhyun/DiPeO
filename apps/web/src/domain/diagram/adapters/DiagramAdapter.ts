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
import { ArrowID, DomainArrow, DomainHandle, DomainNode, NodeID, DomainDiagram, diagramArraysToMaps, NodeType } from '@/infrastructure/types';
import { JsonDict, HandleDirection, HandleLabel } from '@dipeo/models';
import { ContentType } from '@/__generated__/graphql';
import { generateId } from '@/infrastructure/types/utilities';
import { createHandleIndex, getHandlesForNode, findHandleByLabel } from '../utils/handleIndex';
import { Converters } from '@/infrastructure/converters';
import { ValidationService } from '@/infrastructure/services';

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
    content_type?: string | null;
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
  static toReactFlow(diagram: DomainDiagram): {
    nodes: DiPeoNode[];
    edges: DiPeoEdge[];
  } {
    const startTime = performance.now();

    const handleIndex = createHandleIndex(diagram.handles || []);
    const indexTime = performance.now();

    const nodes = (diagram.nodes || []).map((node: DomainNode) => {
      const handles = getHandlesForNode(handleIndex, node.id);
      return this.nodeToReactFlow(node, handles);
    });

    const nodesTime = performance.now();

    const edges = (diagram.arrows || []).map((arrow: DomainArrow) =>
      this.arrowToReactFlow(arrow)
    );

    const endTime = performance.now();

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
    const inputs = handles
      .filter(h => h.direction === HandleDirection.INPUT)
      .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});

    const outputs = handles
      .filter(h => h.direction === HandleDirection.OUTPUT)
      .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});

    const position = node.position &&
                    typeof node.position.x === 'number' &&
                    typeof node.position.y === 'number'
                    ? { x: node.position.x, y: node.position.y }
                    : { x: 0, y: 0 };

    const nodeData = { ...(node.data || {}) };

    if (node.type === NodeType.PERSON_JOB && Array.isArray(nodeData.tools)) {
      nodeData.tools = Converters.toolsArrayToString(nodeData.tools as Array<{ type: string }>);
    }

    return {
      id: node.id,
      type: Converters.nodeTypeToString(node.type),
      position,
      data: {
        ...nodeData,
        label: (nodeData?.label as string) || '',
        inputs,
        outputs,
        _handles: handles
      },
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
    const sourceParsed = Converters.parseHandleId(arrow.source);
    const targetParsed = Converters.parseHandleId(arrow.target);
    const sourceNode = sourceParsed.node_id;
    const targetNode = targetParsed.node_id;

    const sourceHandle = arrow.source;
    const targetHandle = arrow.target;

    const edgeData = { ...(arrow.data || {}) };
    if (arrow.content_type) {
      edgeData.content_type = typeof arrow.content_type === 'string'
        ? arrow.content_type.toLowerCase()
        : arrow.content_type;
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
      id: Converters.toNodeId(rfNode.id),
      type: Converters.stringToNodeType(rfNode.type || 'start'),
      position: { ...rfNode.position },
      data: {
        ...nodeData,
        label: (nodeData.label || rfNode.id) as string
      } as JsonDict
    };
  }

  /**
   * Convert React Flow edge back to domain arrow
   */
  static reactToArrow(rfEdge: RFEdge): DomainArrow {
    const sourceHandleLabel = (rfEdge.sourceHandle || 'default') as HandleLabel;
    const targetHandleLabel = (rfEdge.targetHandle || 'default') as HandleLabel;

    const sourceHandle = Converters.createHandleId(
      Converters.toNodeId(rfEdge.source),
      sourceHandleLabel,
      HandleDirection.OUTPUT
    );
    const targetHandle = Converters.createHandleId(
      Converters.toNodeId(rfEdge.target),
      targetHandleLabel,
      HandleDirection.INPUT
    );

    const { content_type, label, ...restData } = rfEdge.data || {};

    const domainArrow: DomainArrow = {
      id: Converters.toArrowId(rfEdge.id),
      source: sourceHandle,
      target: targetHandle,
      data: Object.keys(restData).length > 0 ? restData : undefined
    };

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

    const sourceHandle = Converters.createHandleId(
      Converters.toNodeId(connection.source),
      sourceHandleLabel,
      HandleDirection.OUTPUT
    );
    const targetHandle = Converters.createHandleId(
      Converters.toNodeId(connection.target),
      targetHandleLabel,
      HandleDirection.INPUT
    );

    return {
      id: Converters.toArrowId(generateId()),
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

    if (connection.source === connection.target) {
      validated.isValid = false;
      validated.validationMessage = 'Cannot connect node to itself';
      return validated;
    }

    const sourceHandleLabel = (connection.sourceHandle || 'default') as HandleLabel;
    const targetHandleLabel = (connection.targetHandle || 'default') as HandleLabel;

    const sourceHandleId = Converters.createHandleId(
      Converters.toNodeId(connection.source),
      sourceHandleLabel,
      HandleDirection.OUTPUT
    );
    const targetHandleId = Converters.createHandleId(
      Converters.toNodeId(connection.target),
      targetHandleLabel,
      HandleDirection.INPUT
    );

    const sourceNode = diagram.nodes.find((n: DomainNode) => n.id === connection.source);
    const targetNode = diagram.nodes.find((n: DomainNode) => n.id === connection.target);

    if (!sourceNode || !targetNode) {
      validated.isValid = false;
      validated.validationMessage = 'Node not found';
      return validated;
    }

    const handleIndex = createHandleIndex(diagram.handles || []);

    const extractHandleLabel = (handleId: string | null): string => {
      if (!handleId) return 'default';
      const parts = handleId.split('_');
      if (parts.length >= 3) {
        return parts[parts.length - 2] || 'default';
      }
      return handleId;
    };

    const sourceLabel = extractHandleLabel(connection.sourceHandle);
    const targetLabel = extractHandleLabel(connection.targetHandle);

    const sourceHandle = findHandleByLabel(
      handleIndex,
      Converters.toNodeId(connection.source),
      sourceLabel
    );
    const targetHandle = findHandleByLabel(
      handleIndex,
      Converters.toNodeId(connection.target),
      targetLabel
    );

    if (!sourceHandle || !targetHandle) {
      console.error('Handle lookup failed:', {
        sourceNode: connection.source,
        sourceHandleId: connection.sourceHandle,
        sourceLabel,
        targetNode: connection.target,
        targetHandleId: connection.targetHandle,
        targetLabel,
        availableHandles: diagram.handles?.map(h => ({
          nodeId: h.node_id,
          label: h.label,
          direction: h.direction
        }))
      });
      validated.isValid = false;
      validated.validationMessage = 'Handle not found';
      return validated;
    }

    const nodesMap = new Map(diagram.nodes.map((n: DomainNode) => [n.id, n]));
    const connectionValidation = ValidationService.validateConnection(sourceHandle.id, targetHandle.id, nodesMap);
    if (!connectionValidation.valid) {
      validated.isValid = false;
      validated.validationMessage = connectionValidation.errors.join('; ');
      return validated;
    }

    const existingArrow = diagram.arrows.find((arrow: DomainArrow) =>
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

  static generateHandles(_node: DomainNode): DomainHandle[] {
    return [];
  }



  /**
   * Convert array of React Flow nodes to domain nodes
   */
  static reactNodesToDomain(rfNodes: RFNode[]): Map<NodeID, DomainNode> {
    const domainNodes = rfNodes.map(rfNode => this.reactToNode(rfNode));
    return diagramArraysToMaps({
      nodes: domainNodes,
      arrows: [],
      handles: [],
      persons: []
    }).nodes;
  }

  /**
   * Convert array of React Flow edges to domain arrows
   */
  static reactEdgesToDomain(rfEdges: RFEdge[]): Map<ArrowID, DomainArrow> {
    const domainArrows = rfEdges.map(rfEdge => this.reactToArrow(rfEdge));
    return diagramArraysToMaps({
      nodes: [],
      arrows: domainArrows,
      handles: [],
      persons: []
    }).arrows;
  }
}
