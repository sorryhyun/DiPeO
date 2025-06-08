import { HandleID, NodeID } from '../branded';
import { DataType, HandlePosition } from '../enums';

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
 * Type guards
 */
export function isDomainHandle(obj: unknown): obj is DomainHandle {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'nodeId' in obj &&
    'name' in obj &&
    'direction' in obj &&
    'dataType' in obj
  );
}

export function isInputHandle(handle: DomainHandle): handle is InputHandle {
  return handle.direction === 'input';
}

export function isOutputHandle(handle: DomainHandle): handle is OutputHandle {
  return handle.direction === 'output';
}

/**
 * Handle compatibility checker
 */
export function areHandlesCompatible(
  source: DomainHandle,
  target: DomainHandle
): boolean {
  // Source must be output, target must be input
  if (!isOutputHandle(source) || !isInputHandle(target)) {
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