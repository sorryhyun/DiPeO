import type { Node, Edge, Connection } from '@xyflow/react';
import { DomainDiagram, DomainNode, DomainArrow } from '../graphql-mappings';
import { NodeID, ArrowID } from '../branded';

/**
 * React specific diagram representation
 */
export interface ReactDiagram {
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