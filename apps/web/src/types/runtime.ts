// types/runtime.ts - Runtime/Execution types

import type { ID, Dict } from './primitives';

export type MessageHandler = (message: WSMessage) => void;

export interface ExecutionOptions {
  mode?: 'monitor' | 'headless' | 'check';
  debug?: boolean;
  delay?: number;
  continueOnError?: boolean;
  allowPartial?: boolean;
  debugMode?: boolean;
}

export interface ExecutionState<C = Dict> {
  id: ID;
  running: ID[];
  completed: ID[];
  skipped: ID[];
  paused: ID[];
  context: C;
  errors: Dict<string>;
  isRunning: boolean;
  startedAt?: string;
  endedAt?: string;
  totalTokens?: number;
}

export interface WebSocketHooks {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (e: Event) => void;
  onMessage?: (ev: MessageEvent) => void;
}

export interface WebSocketClientOptions extends WebSocketHooks {
  url?: string;
  protocols?: string[];
  reconnectInterval?: number;
  maxReconnect?: number;
  maxReconnectAttempts?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  debug?: boolean;
}

/* Event helpers */
export type EventPayload<T extends string, P = undefined> =
  P extends undefined ? { type: T } : { type: T; payload: P };

export type NodeExecutionEvent =
  | EventPayload<'node_start', { nodeId: ID }>
  | EventPayload<'node_progress', { nodeId: ID; message?: string }>
  | EventPayload<'node_complete', { nodeId: ID; output: unknown }>
  | EventPayload<'node_error', { nodeId: ID; error: string }>
  | EventPayload<'node_paused', { nodeId: ID }>
  | EventPayload<'node_resumed', { nodeId: ID }>
  | EventPayload<'node_skipped', { nodeId: ID }>;

// WebSocket message types
export type WSMessage = { type: string; [key: string]: any };

/* Execution update types */
export interface ExecutionUpdate {
  type: string;
  executionId?: string;
  node_id?: string;
  progress?: string;
  output?: unknown;
  output_preview?: string;
  error?: string;
  status?: string;
  total_nodes?: number;
  context?: Dict;
  duration?: number;
  nodeType?: string;
  nodeId?: string;
  message?: string;
  details?: Dict;
  totalTokens?: number;
  tokens?: number;
  timestamp?: string;
  conversationId?: string;
}

export interface InteractivePromptData {
  nodeId: string;
  prompt: string;
  timeout?: number;
  executionId?: string;
  context?: Dict;
}

/* Monitor mode */
export interface MonitorSubscription {
  executionId: string;
}

export interface ExecutionResult {
  success?: boolean;
  executionId?: string;
  context?: Record<string, unknown>;
  totalTokens?: number;
  duration?: number;
  finalContext?: Record<string, any>;
  error?: string;
  metadata?: {
    totalTokens?: number;
    executionTime?: number;
  };
}