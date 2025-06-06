import { Node } from '@xyflow/react';
import type { Node as DiagramNode } from '@/types';

/**
 * Unified node utilities - all node operations in one place
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

/**
 * Get node data with defaults
 */
export const getNodeData = (node: DiagramNode, defaults: Record<string, any> = {}): Record<string, any> => {
  return { ...defaults, ...node.data };
};