import { DomainNode } from '@/types';

// Import factory and utilities
import { 
  createNodeBuilders,
  capitalize,
  detectVariables,
  type NodeInfo,
  type NodeBuilder,
  type NodeWithHandles
} from './nodeBuilderFactory';

// Re-export types and utilities for backward compatibility
export { capitalize, detectVariables, type NodeInfo, type NodeBuilder };

// Create node builders using the factory
export const NODE_BUILDERS: Record<string, NodeBuilder> = createNodeBuilders();

/**
 * Build a node using the unified builder system
 */
export function buildNode(info: NodeInfo): NodeWithHandles {
  const nodeType = info.type || 'generic';
  const builder = NODE_BUILDERS[nodeType] || NODE_BUILDERS.generic;
  if (!builder) {
    throw new Error(`No builder found for node type: ${nodeType}`);
  }
  return builder(info);
}

/**
 * Build multiple nodes from a record of node infos
 */
export function buildNodes(nodeInfos: Record<string, NodeInfo>): DomainNode[] {
  return Object.values(nodeInfos).map(info => buildNode(info));
}


