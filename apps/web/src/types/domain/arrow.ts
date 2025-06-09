import { ArrowID, HandleID } from '../branded';
import { parseHandleId } from './handle';

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