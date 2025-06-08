import { ArrowID, HandleID } from '../branded';

/**
 * Pure domain arrow - framework-agnostic connection
 * Connects handles using the format "nodeId:handleName"
 */
export interface DomainArrow {
  id: ArrowID;
  source: HandleID;
  target: HandleID;
  data?: Record<string, unknown>;
}

/**
 * Arrow with validation metadata
 */
export interface ValidatedArrow extends DomainArrow {
  isValid: boolean;
  validationErrors?: string[];
}

/**
 * Type guard for domain arrows
 */
export function isDomainArrow(obj: unknown): obj is DomainArrow {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'source' in obj &&
    'target' in obj &&
    typeof (obj as any).source === 'string' &&
    typeof (obj as any).target === 'string' &&
    (obj as any).source.includes(':') &&
    (obj as any).target.includes(':')
  );
}

/**
 * Extract node ID and handle name from a handle ID
 */
export function parseHandleId(handleId: HandleID): { nodeId: string; handleName: string } {
  const [nodeId, handleName] = handleId.split(':');
  if (!nodeId || !handleName) {
    throw new Error(`Invalid handle ID format: ${handleId}`);
  }
  return { nodeId, handleName };
}

/**
 * Check if an arrow connects two specific nodes
 */
export function connectsNodes(
  arrow: DomainArrow,
  sourceNodeId: string,
  targetNodeId: string
): boolean {
  const source = parseHandleId(arrow.source);
  const target = parseHandleId(arrow.target);
  return source.nodeId === sourceNodeId && target.nodeId === targetNodeId;
}