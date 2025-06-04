import { Node } from '@xyflow/react';

/**
 * Utility functions for node operations
 */

export const createNodeId = (): string => {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const getNodeDisplayName = (node: Node): string => {
  const data = node.data as { label?: string; name?: string };
  return data?.label || data?.name || node.type || 'Unnamed Node';
};

export function createHandleId(nodeId: string, type: string, name?: string): string {
  return name ? `${nodeId}-${type}-${name}` : `${nodeId}-${type}`;
}