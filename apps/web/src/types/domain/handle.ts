import { HandleID, NodeID } from '../branded';
import { DataType, HandlePosition } from '../primitives';


export type HandleDirection = 'input' | 'output';

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

export interface InputHandle extends DomainHandle {
  direction: 'input';
  required?: boolean;
  defaultValue?: unknown;
}

export interface OutputHandle extends DomainHandle {
  direction: 'output';
  dynamic?: boolean;
}

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
  if (source.dataType === 'any' || target.dataType === 'any') {
    return true;
  }

  // Same types are compatible
  return source.dataType === target.dataType;
}

export function createHandleId(nodeId: NodeID, handleName: string): HandleID {
  return `${nodeId}:${handleName}` as HandleID;
}

export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  const [nodeId, ...handleNameParts] = handleId.split(':');
  return {
    nodeId: nodeId as NodeID,
    handleName: handleNameParts.join(':')
  };
}

export function isValidHandleIdFormat(value: string): boolean {
  return /^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$/.test(value);
}

export function isValidNodeIdFormat(value: string): boolean {
  return /^[a-zA-Z0-9_-]+$/.test(value);
}
