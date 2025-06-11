import { ArrowID, HandleID } from '../branded';
import { parseHandleId } from './handle';
import type React from "react";


export interface DomainArrow {
  id: ArrowID;
  source: HandleID;
  target: HandleID;
  data?: Record<string, unknown>;
}


export interface ValidatedArrow extends DomainArrow {
  isValid: boolean;
  validationErrors?: string[];
}

export type ArrowData = {
  label?: string;
  style?: React.CSSProperties;
};

export function connectsHandles(
  arrow: DomainArrow,
  sourceHandle: HandleID,
  targetHandle: HandleID
): boolean {
  return arrow.source === sourceHandle && arrow.target === targetHandle;
}

export function connectsNodes(
  arrow: DomainArrow,
  sourceNodeId: string,
  targetNodeId: string
): boolean {
  const source = parseHandleId(arrow.source);
  const target = parseHandleId(arrow.target);
  return source.nodeId === sourceNodeId && target.nodeId === targetNodeId;
}

export function connectsToNode(
  arrow: DomainArrow,
  nodeId: string
): boolean {
  const source = parseHandleId(arrow.source);
  const target = parseHandleId(arrow.target);
  return source.nodeId === nodeId || target.nodeId === nodeId;
}