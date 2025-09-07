/**
 * Handle indexing utilities for performance optimization
 *
 * These utilities provide O(1) lookup performance for handle operations
 * by pre-indexing handles by node_id instead of filtering arrays.
 */

import { DomainHandle, NodeID } from '@/infrastructure/types';

/**
 * Creates an index of handles grouped by node_id for O(1) lookups
 */
export function createHandleIndex(handles: DomainHandle[]): Map<NodeID, DomainHandle[]> {
  const index = new Map<NodeID, DomainHandle[]>();

  for (const handle of handles) {
    const nodeHandles = index.get(handle.node_id) || [];
    nodeHandles.push(handle);
    index.set(handle.node_id, nodeHandles);
  }

  return index;
}

/**
 * Gets handles for a specific node from the index
 */
export function getHandlesForNode(
  handleIndex: Map<NodeID, DomainHandle[]>,
  nodeId: NodeID
): DomainHandle[] {
  return handleIndex.get(nodeId) || [];
}

/**
 * Finds a specific handle by node_id and label
 */
export function findHandleByLabel(
  handleIndex: Map<NodeID, DomainHandle[]>,
  nodeId: NodeID,
  label: string
): DomainHandle | undefined {
  const nodeHandles = handleIndex.get(nodeId);
  if (!nodeHandles) return undefined;

  return nodeHandles.find(h => h.label === label);
}

/**
 * Groups handles by node ID for optimized lookups
 * Alternative implementation using forEach pattern
 */
export function groupHandlesByNode(handles: DomainHandle[]): Map<NodeID, DomainHandle[]> {
  const grouped: Record<string, DomainHandle[]> = {};
  handles.forEach(handle => {
    const nodeId = handle.node_id;
    if (!grouped[nodeId]) grouped[nodeId] = [];
    grouped[nodeId].push(handle);
  });
  return new Map(Object.entries(grouped)) as Map<NodeID, DomainHandle[]>;
}

/**
 * Performance benchmark helper
 */
export function benchmarkHandleLookup(
  name: string,
  operation: () => void
): number {
  const start = performance.now();
  operation();
  const end = performance.now();
  const duration = end - start;

  if (import.meta.env.DEV) {
    console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms`);
  }

  return duration;
}
