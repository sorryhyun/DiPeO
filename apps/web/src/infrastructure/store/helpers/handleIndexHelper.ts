import { DomainHandle, HandleID, NodeID } from '@/infrastructure/types';

/**
 * Rebuilds the handle index from the handles Map
 * This provides O(1) lookups for handles by node ID
 */
export function rebuildHandleIndex(
  handles: Map<HandleID, DomainHandle>
): Map<NodeID, DomainHandle[]> {
  const index = new Map<NodeID, DomainHandle[]>();
  
  handles.forEach(handle => {
    const nodeHandles = index.get(handle.node_id) || [];
    nodeHandles.push(handle);
    index.set(handle.node_id, nodeHandles);
  });
  
  return index;
}

/**
 * Updates the handle index when handles are added or removed
 */
export function updateHandleIndex(
  handleIndex: Map<NodeID, DomainHandle[]>,
  handles: Map<HandleID, DomainHandle>
): void {
  // Clear and rebuild the index
  handleIndex.clear();
  
  handles.forEach(handle => {
    const nodeHandles = handleIndex.get(handle.node_id) || [];
    if (nodeHandles.length === 0) {
      handleIndex.set(handle.node_id, nodeHandles);
    }
    nodeHandles.push(handle);
  });
}