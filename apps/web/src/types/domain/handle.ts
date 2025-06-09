import { HandleID, NodeID } from '../branded';
import { DataType, HandlePosition } from '../primitives';

/**
 * Handle direction - aligned terminology
 */
export type HandleDirection = 'input' | 'output';

/**
 * Pure domain handle - framework-agnostic port definition
 */
export interface DomainHandle {
  id: HandleID;
  nodeId: NodeID;
  name: string;
  direction: HandleDirection;
  dataType: DataType;
  position?: HandlePosition;
  offset?: number;
  label?: string;
  maxConnections?: number;
}

/**
 * Input handle specification
 */
export interface InputHandle extends DomainHandle {
  direction: 'input';
  required?: boolean;
  defaultValue?: unknown;
}

/**
 * Output handle specification
 */
export interface OutputHandle extends DomainHandle {
  direction: 'output';
  dynamic?: boolean;
}

/**
 * Handle compatibility checker
 */
export function areHandlesCompatible(
  source: DomainHandle,
  target: DomainHandle
): boolean {
  // Source must be output, target must be input
  if (source.direction !== 'output' || target.direction !== 'input') {
    return false;
  }

  // Check data type compatibility
  // 'any' type is compatible with everything
  if (source.dataType === DataType.Any || target.dataType === DataType.Any) {
    return true;
  }

  // Same types are compatible
  return source.dataType === target.dataType;
}

/**
 * Generate handle ID from node ID and handle name
 */
export function createHandleId(nodeId: NodeID, handleName: string): HandleID {
  return `${nodeId}:${handleName}` as HandleID;
}

/**
 * Parse handle ID into node ID and handle name
 */
export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  const [nodeId, ...handleNameParts] = handleId.split(':');
  return {
    nodeId: nodeId as NodeID,
    handleName: handleNameParts.join(':')
  };
}

/**
 * Validate handle ID format
 */
export function isValidHandleIdFormat(value: string): boolean {
  return /^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$/.test(value);
}

/**
 * Validate node ID format
 */
export function isValidNodeIdFormat(value: string): boolean {
  return /^[a-zA-Z0-9_-]+$/.test(value);
}
