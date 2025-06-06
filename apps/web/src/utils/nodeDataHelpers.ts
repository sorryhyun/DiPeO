import { Node } from '@/types';

export const getNodeData = (node: Node, defaults: Record<string, any> = {}): Record<string, any> => {
  return { ...defaults, ...node.data };
};