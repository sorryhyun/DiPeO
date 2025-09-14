/**
 * Subscription payload types for GraphQL subscriptions
 */

import { NodeID } from './diagram';
import { ExecutionID, ExecutionUpdate } from './execution';
import { EventType, Status } from './enums';

/**
 * Node update payload for node-specific updates
 */
export interface NodeUpdate {
  execution_id: ExecutionID;
  node_id: NodeID;
  status: Status;
  progress?: number;
  output?: any;
  error?: string;
  metrics?: Record<string, any>;
  timestamp: string;
}

/**
 * Interactive prompt payload for user interaction requests
 */
export interface InteractivePrompt {
  execution_id: ExecutionID;
  node_id: NodeID;
  prompt_id: string;
  prompt: string;
  timeout?: number;
  default_value?: string | null;
  options?: string[];
  timestamp: string;
}

/**
 * Execution log entry for real-time log streaming
 */
export interface ExecutionLogEntry {
  execution_id: ExecutionID;
  node_id?: NodeID;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  message: string;
  context?: Record<string, any>;
  timestamp: string;
}

/**
 * Keepalive payload for connection maintenance
 */
export interface KeepalivePayload {
  type: 'keepalive';
  timestamp: string;
}

/**
 * Union type for all subscription payloads
 */
export type SubscriptionPayload =
  | ExecutionUpdate
  | NodeUpdate
  | InteractivePrompt
  | ExecutionLogEntry
  | KeepalivePayload;
