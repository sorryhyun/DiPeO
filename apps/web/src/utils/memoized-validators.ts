/**
 * Memoized validation functions for performance optimization
 */

import { memoize } from 'lodash-es';
import type { DataType } from '@/types/handles';

/**
 * Check if two data types are compatible for connection
 * Memoized to avoid repeated computation for the same type pairs
 */
export const areTypesCompatible = memoize(
  (from: DataType | undefined, to: DataType | undefined): boolean => {
    // No type info means compatible
    if (!from || !to) return true;
    
    // 'any' is compatible with everything
    if (from === 'any' || to === 'any') return true;
    
    // Direct match
    if (from === to) return true;
    
    // Custom type matching
    if (typeof from === 'object' && typeof to === 'object') {
      return from.custom === to.custom;
    }
    
    return false;
  },
  // Custom cache key generator
  (from, to) => `${JSON.stringify(from)}:${JSON.stringify(to)}`
);

/**
 * Check if a string is a valid node ID format
 * Memoized for repeated validation of the same strings
 */
export const isValidNodeIdFormat = memoize(
  (id: string): boolean => {
    return /^[a-zA-Z0-9_-]+$/.test(id);
  }
);

/**
 * Check if a string is a valid handle ID format
 * Memoized for repeated validation of the same strings
 */
export const isValidHandleIdFormat = memoize(
  (id: string): boolean => {
    return /^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$/.test(id);
  }
);

/**
 * Parse handle ID to extract components
 * Memoized to avoid repeated string splitting
 */
export const parseHandleIdMemoized = memoize(
  (id: string): { nodeId: string; handleName: string } | null => {
    const parts = id.split(':');
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      return null;
    }
    return { nodeId: parts[0], handleName: parts[1] };
  }
);

/**
 * Check if a node type supports handles
 * Memoized for repeated checks of the same node type
 */
export const nodeTypeSupportsHandles = memoize(
  (nodeType: string): boolean => {
    const typesWithoutHandles = new Set(['text', 'annotation', 'group']);
    return !typesWithoutHandles.has(nodeType);
  }
);

/**
 * Get default handle positions for a node type
 * Memoized to avoid repeated object creation
 */
export const getDefaultHandlePositions = memoize(
  (nodeType: string): { input: string; output: string } => {
    const specialPositions: Record<string, { input: string; output: string }> = {
      condition: { input: 'left', output: 'right' },
      db: { input: 'top', output: 'bottom' },
      notion: { input: 'top', output: 'bottom' },
    };
    
    return specialPositions[nodeType] || { input: 'left', output: 'right' };
  }
);

/**
 * Check if a connection would create a cycle
 * Note: This is not memoized as diagram state changes frequently
 * and memoization would require complex cache invalidation
 */
export function wouldCreateCycle(
  sourceNodeId: string,
  targetNodeId: string,
  edges: Array<{ source: string; target: string }>
): boolean {
  // Build adjacency list
  const adjacency = new Map<string, Set<string>>();
  for (const edge of edges) {
    if (!adjacency.has(edge.source)) {
      adjacency.set(edge.source, new Set());
    }
    adjacency.get(edge.source)!.add(edge.target);
  }
  
  // Check if adding this edge would create a path from target to source
  const visited = new Set<string>();
  const queue = [targetNodeId];
  
  while (queue.length > 0) {
    const current = queue.shift()!;
    if (current === sourceNodeId) {
      return true; // Would create cycle
    }
    
    if (visited.has(current)) continue;
    visited.add(current);
    
    const neighbors = adjacency.get(current);
    if (neighbors) {
      for (const neighbor of neighbors) {
        queue.push(neighbor);
      }
    }
  }
  
  return false;
}

// Clear memoization caches when needed (e.g., during hot reload)
export function clearValidationCaches(): void {
  areTypesCompatible.cache.clear?.();
  isValidNodeIdFormat.cache.clear?.();
  isValidHandleIdFormat.cache.clear?.();
  parseHandleIdMemoized.cache.clear?.();
  nodeTypeSupportsHandles.cache.clear?.();
  getDefaultHandlePositions.cache.clear?.();
}