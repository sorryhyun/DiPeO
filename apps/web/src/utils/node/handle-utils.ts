/**
 * Handle utility functions for working with the domain model
 * 
 * In the new architecture, handles are stored separately in the diagram,
 * not directly on nodes. All functions now require a DomainDiagram parameter
 * to access handle information.
 */

import { NodeID, HandleID } from '@/types/branded';
import { NodeKind } from '@/types/primitives';
import { DomainDiagram, DomainHandle, InputHandle, OutputHandle } from '@/types/domain';
import { createHandleId } from '@/types/domain/handle';
import { getNodeHandles as getDiagramNodeHandles } from '@/types/domain/diagram';
import { getHandleConfig } from '@/config/handleRegistry';

/**
 * Error thrown when a handle is not found
 */
export class HandleNotFoundError extends Error {
  constructor(nodeId: NodeID, handleName: string) {
    super(`Handle "${handleName}" not found on node ${nodeId}`);
    this.name = 'HandleNotFoundError';
  }
}

/**
 * Get a specific input handle from a node
 */
export function getInputHandle(
  diagram: DomainDiagram,
  nodeId: NodeID,
  handleName: string
): InputHandle {
  const handleId = createHandleId(nodeId, handleName);
  const handle = diagram.handles[handleId];
  
  if (!handle || handle.direction !== 'input') {
    throw new HandleNotFoundError(nodeId, handleName);
  }
  
  return handle as InputHandle;
}

/**
 * Get a specific output handle from a node
 */
export function getOutputHandle(
  diagram: DomainDiagram,
  nodeId: NodeID,
  handleName: string
): OutputHandle {
  const handleId = createHandleId(nodeId, handleName);
  const handle = diagram.handles[handleId];
  
  if (!handle || handle.direction !== 'output') {
    throw new HandleNotFoundError(nodeId, handleName);
  }
  
  return handle as OutputHandle;
}

/**
 * Get all input handles from a node
 */
export function getInputHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): InputHandle[] {
  const handles = getDiagramNodeHandles(diagram, nodeId);
  return handles.filter((h): h is InputHandle => h.direction === 'input');
}

/**
 * Get all output handles from a node
 */
export function getOutputHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): OutputHandle[] {
  const handles = getDiagramNodeHandles(diagram, nodeId);
  return handles.filter((h): h is OutputHandle => h.direction === 'output');
}

/**
 * Check if a node has a specific input handle
 */
export function hasInputHandle(
  diagram: DomainDiagram,
  nodeId: NodeID,
  handleName: string
): boolean {
  const handleId = createHandleId(nodeId, handleName);
  const handle = diagram.handles[handleId];
  return handle !== undefined && handle.direction === 'input';
}

/**
 * Check if a node has a specific output handle
 */
export function hasOutputHandle(
  diagram: DomainDiagram,
  nodeId: NodeID,
  handleName: string
): boolean {
  const handleId = createHandleId(nodeId, handleName);
  const handle = diagram.handles[handleId];
  return handle !== undefined && handle.direction === 'output';
}

/**
 * Get handle ID from node and handle name
 */
export function getHandleId(nodeId: NodeID, handleName: string): HandleID {
  return createHandleId(nodeId, handleName);
}

/**
 * Find handle by ID in a diagram
 */
export function findHandleById(
  diagram: DomainDiagram,
  handleId: HandleID
): DomainHandle | undefined {
  return diagram.handles[handleId];
}

/**
 * Get all handles (both input and output) from a node
 */
export function getAllHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): DomainHandle[] {
  return getDiagramNodeHandles(diagram, nodeId);
}

/**
 * Count handles on a node
 */
export function countHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): {
  inputs: number;
  outputs: number;
  total: number;
} {
  const handles = getDiagramNodeHandles(diagram, nodeId);
  const inputCount = handles.filter(h => h.direction === 'input').length;
  const outputCount = handles.filter(h => h.direction === 'output').length;
  
  return {
    inputs: inputCount,
    outputs: outputCount,
    total: inputCount + outputCount
  };
}

/**
 * Get handle names for a specific node type
 */
export function getHandleNamesForType(
  nodeType: NodeKind
): {
  inputs: string[];
  outputs: string[];
} {
  const config = getHandleConfig(nodeType);
  
  const inputs = config.inputs?.map(h => h.id) || [];
  const outputs = config.outputs?.map(h => h.id) || [];
  
  return { inputs, outputs };
}

/**
 * Validate if a handle name is valid for a node type
 */
export function isValidHandleName(
  nodeType: NodeKind,
  handleName: string,
  direction: 'input' | 'output'
): boolean {
  const config = getHandleConfig(nodeType);
  const handles = direction === 'input' ? config.inputs : config.outputs;
  return handles?.some(h => h.id === handleName) || false;
}

/**
 * Get handle position offset for visual alignment
 * This information is now stored in the handle registry
 */
export function getHandleOffset(
  nodeType: NodeKind,
  handleName: string
): { x: number; y: number } | undefined {
  const config = getHandleConfig(nodeType);
  const allHandles = [...(config.inputs || []), ...(config.outputs || [])];
  const handle = allHandles.find(h => h.id === handleName);
  
  if (handle?.offset) {
    return {
      x: handle.offset.x || 0,
      y: handle.offset.y || 0
    };
  }
  
  return undefined;
}