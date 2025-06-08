import type { Node, Edge, Connection } from 'reactflow';
import { DomainDiagram, DomainNode, DomainArrow } from '../domain';
import { NodeID, ArrowID } from '../branded';

/**
 * React Flow specific diagram representation
 */
export interface ReactFlowDiagram {
  nodes: Node[];
  edges: Edge[];
}

/**
 * React Flow node with DiPeO data
 */
export interface DiPeoNode extends Node {
  data: {
    label?: string;
    properties: Record<string, unknown>;
    inputs?: Record<string, unknown>;
    outputs?: Record<string, unknown>;
  };
}

/**
 * React Flow edge with DiPeO data
 */
export interface DiPeoEdge extends Edge {
  data?: {
    label?: string;
    dataType?: string;
    [key: string]: unknown;
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
 * React Flow instance wrapper
 */
export interface DiPeoReactFlowInstance {
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
  return node && typeof node.data === 'object' && 'properties' in node.data;
}

export function isDiPeoEdge(edge: Edge): edge is DiPeoEdge {
  return edge && typeof edge === 'object';
}