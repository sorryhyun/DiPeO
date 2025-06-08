// Handle adapter for converting between handle-based arrows and ReactFlow edges

import type { Arrow, ReactFlowEdge, HandleID } from '@/types';

/**
 * Parse a handle ID to extract node ID and handle name
 * @param handleId Format: "nodeId:handleName"
 */
export function parseHandleId(handleId: string): { nodeId: string; handleName: string } {
  const [nodeId = '', ...handleParts] = handleId.split(':');
  const handleName = handleParts.join(':') || 'default'; // Handle case where handle name contains ':' or is missing
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

