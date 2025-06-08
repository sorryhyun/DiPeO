// Handle adapter for converting between handle-based arrows and ReactFlow edges

import type { Arrow, ReactFlowEdge, HandleID, Handle } from '@/types';

/**
 * Parse a handle ID to extract node ID and handle name
 * @param handleId Format: "nodeId:handleName"
 */
export function parseHandleId(handleId: string): { nodeId: string; handleName: string } {
  const [nodeId, ...handleParts] = handleId.split(':');
  const handleName = handleParts.join(':'); // Handle case where handle name contains ':'
  return { nodeId, handleName };
}

/**
 * Create a handle ID from node ID and handle name
 */
export function createHandleId(nodeId: string, handleName: string): HandleID {
  return `${nodeId}:${handleName}` as HandleID;
}

/**
 * Convert our handle-based arrow to ReactFlow edge format
 */
export function arrowToReactFlowEdge(arrow: Arrow): ReactFlowEdge {
  const { nodeId: sourceNodeId, handleName: sourceHandleName } = parseHandleId(arrow.source);
  const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);
  
  return {
    id: arrow.id,
    source: sourceNodeId,
    target: targetNodeId,
    sourceHandle: sourceHandleName,
    targetHandle: targetHandleName,
    data: arrow.data,
  };
}

/**
 * Convert ReactFlow edge to our handle-based arrow format
 */
export function reactFlowEdgeToArrow(
  edge: ReactFlowEdge,
  sourceHandle?: string,
  targetHandle?: string
): Arrow {
  // Use provided handle names or default to 'output' and 'input'
  const sourceHandleName = sourceHandle || edge.sourceHandle || 'output';
  const targetHandleName = targetHandle || edge.targetHandle || 'input';
  
  return {
    id: edge.id,
    source: createHandleId(edge.source, sourceHandleName),
    target: createHandleId(edge.target, targetHandleName),
    data: edge.data,
  };
}

/**
 * Validate if a handle ID exists in the node's handles
 */
export function validateHandleExists(handleId: string, handles: Handle[]): boolean {
  return handles.some(h => h.id === handleId);
}

/**
 * Get handle by ID from a list of handles
 */
export function getHandleById(handleId: string, handles: Handle[]): Handle | undefined {
  return handles.find(h => h.id === handleId);
}

/**
 * Check if two handles can be connected based on their types
 */
export function canConnectHandles(sourceHandle: Handle, targetHandle: Handle): boolean {
  // Basic validation: source must connect to target
  if (sourceHandle.kind !== 'source' || targetHandle.kind !== 'target') {
    return false;
  }
  
  // Type compatibility check
  if (!sourceHandle.dataType || !targetHandle.dataType || targetHandle.dataType === 'any') {
    return true;
  }
  
  if (sourceHandle.dataType === 'any') {
    return true;
  }
  
  return sourceHandle.dataType === targetHandle.dataType;
}

/**
 * Convert legacy arrow format (with node IDs) to new handle-based format
 */
export function migrateLegacyArrow(arrow: any, nodes: any[]): Arrow | null {
  // If arrow already uses handle IDs, return as is
  if (arrow.source?.includes(':') && arrow.target?.includes(':')) {
    return {
      id: arrow.id,
      source: arrow.source,
      target: arrow.target,
      data: arrow.data || {}
    };
  }
  
  // Legacy format: source/target are node IDs
  const sourceNode = nodes.find(n => n.id === arrow.source);
  const targetNode = nodes.find(n => n.id === arrow.target);
  
  if (!sourceNode || !targetNode) {
    console.warn(`Cannot migrate arrow ${arrow.id}: source or target node not found`);
    return null;
  }
  
  // Use sourceHandle/targetHandle if provided, otherwise use defaults
  const sourceHandleName = arrow.sourceHandle || 'output';
  const targetHandleName = arrow.targetHandle || 'input';
  
  return {
    id: arrow.id,
    source: createHandleId(sourceNode.id, sourceHandleName),
    target: createHandleId(targetNode.id, targetHandleName),
    data: arrow.data || {}
  };
}