/**
 * Node specification registry
 * Auto-discovery system for node specifications
 */

import { NodeSpecification, NodeSpecificationRegistry } from './node-specification.js';

// Import all node specifications from the nodes module
import * as nodeSpecs from './nodes/index.js';

/**
 * Automatically build the node registry from all imported node specifications.
 * This eliminates the need to manually maintain a registry mapping when adding new node types.
 *
 * The registry is built by:
 * 1. Scanning all exports from './nodes/index.js'
 * 2. Filtering for objects that match the NodeSpecification interface
 * 3. Using the nodeType property as the registry key
 */
export const nodeSpecificationRegistry: NodeSpecificationRegistry = Object.values(nodeSpecs)
  .filter((spec): spec is NodeSpecification =>
    spec !== null &&
    typeof spec === 'object' &&
    'nodeType' in spec &&
    typeof spec.nodeType === 'string'
  )
  .reduce((acc, spec) => {
    acc[spec.nodeType] = spec;
    return acc;
  }, {} as NodeSpecificationRegistry);

// Export convenience function to get a specification by node type
export function getNodeSpecification(nodeType: string): NodeSpecification | undefined {
  return nodeSpecificationRegistry[nodeType];
}

// Export all node specifications for convenience
export * from './nodes/index.js';
