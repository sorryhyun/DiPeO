import { Node } from '@xyflow/react';

/**
 * Utility functions for node operations
 */

export const createNodeId = (): string => {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const getNodePosition = (node: Node) => {
  return {
    x: node.position?.x || 0,
    y: node.position?.y || 0,
  };
};

export const isNodeValid = (node: Node): boolean => {
  return !!(node.id && node.type && node.data);
};

export const getNodeDisplayName = (node: Node): string => {
  const data = node.data as any;
  return data?.label || data?.name || node.type || 'Unnamed Node';
};

export const getNodeConnections = (_node: Node, _allNodes: Node[]) => {
  // This could be expanded to analyze connections between nodes
  return {
    incoming: [],
    outgoing: [],
  };
};

export function createHandleId(nodeId: string, type: string, name?: string): string {
  return name ? `${nodeId}-${type}-${name}` : `${nodeId}-${type}`;
}