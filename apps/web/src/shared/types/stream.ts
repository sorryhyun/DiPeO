// Streaming types

export interface StreamContext {
  executionId: string;
  outputFormat: 'sse' | 'websocket' | 'both';
  createdAt: Date;
}

export interface StreamUpdate {
  type: StreamUpdateType;
  executionId: string;
  nodeId?: string;
  data: unknown;
  timestamp: Date;
}

export type StreamUpdateType =
  | 'execution_started'
  | 'node_started'
  | 'node_completed'
  | 'node_failed'
  | 'execution_completed'
  | 'execution_failed'
  | 'progress_update'
  | 'cost_update'
  | 'message_chunk';