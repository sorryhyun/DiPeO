import type { NodeID } from '../branded';

export type EventPayload<T extends string, P = undefined> =
  P extends undefined ? { type: T } : { type: T; payload: P };

export type NodeExecutionEvent =
  | EventPayload<'node_start', { nodeId: NodeID }>
  | EventPayload<'node_progress', { nodeId: NodeID; message?: string }>
  | EventPayload<'node_complete', { nodeId: NodeID; output: unknown }>
  | EventPayload<'node_error', { nodeId: NodeID; error: string }>
  | EventPayload<'node_paused', { nodeId: NodeID }>
  | EventPayload<'node_resumed', { nodeId: NodeID }>
  | EventPayload<'node_skipped', { nodeId: NodeID }>;