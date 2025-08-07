/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import type { NodeID, DiagramID } from './diagram.js';
import type { Message } from './conversation.js';
import { Status, EventType } from './enums/execution.js';

export type ExecutionID = string & { readonly __brand: 'ExecutionID' };

export { Status, EventType };

export interface TokenUsage {
  input: number;
  output: number;
  cached?: number | null;
  total?: number;
}

export interface NodeState {
  status: Status;
  started_at?: string | null;
  ended_at?: string | null;
  error?: string | null;
  token_usage?: TokenUsage | null;
  output?: Record<string, any> | null;
}

export interface NodeMetrics {
  node_id: string;
  node_type: string;
  start_time: number;
  end_time?: number | null;
  duration_ms?: number | null;
  memory_usage?: number | null;
  token_usage?: TokenUsage | null;
  error?: string | null;
  dependencies?: string[];
}

export interface ExecutionMetrics {
  execution_id: ExecutionID;
  start_time: number;
  end_time?: number | null;
  total_duration_ms?: number | null;
  node_metrics: Record<string, NodeMetrics>;
  critical_path?: string[];
  parallelizable_groups?: string[][];
  bottlenecks?: Array<{
    node_id: string;
    node_type: string;
    duration_ms: number;
    percentage: number;
  }>;
}


export interface ExecutionState {
  id: ExecutionID;
  status: Status;
  diagram_id?: DiagramID | null;
  started_at: string;
  ended_at?: string | null;
  node_states: Record<string, NodeState>;
  node_outputs: Record<string, Record<string, any>>;
  token_usage: TokenUsage;
  error?: string | null;
  variables?: Record<string, any>;
  duration_seconds?: number | null;
  is_active?: boolean;
  exec_counts: Record<string, number>;
  executed_nodes: string[];
  metrics?: ExecutionMetrics | null;
}



export interface ExecutionOptions {
  mode?: 'normal' | 'debug' | 'monitor';
  timeout?: number;
  variables?: Record<string, any>;
  debug?: boolean;
}

export interface InteractivePromptData {
  node_id: NodeID;
  prompt: string;
  timeout?: number;
  default_value?: string | null;
}

export interface InteractiveResponse {
  node_id: NodeID;
  response: string;
  timestamp: string;
}

export type PersonMemoryMessage = Message;

export interface ExecutionUpdate {
  type: EventType;
  execution_id: ExecutionID;
  node_id?: NodeID;
  status?: Status;
  result?: any;
  error?: string;
  timestamp?: string;
  total_tokens?: number;
  node_type?: string;
  tokens?: number;
  data?: Record<string, any>;
}


export interface NodeDefinition {
  type: string;
  node_schema: any;
  handler: any;
  requires_services?: string[];
  description?: string;
}


export function createTokenUsage(input: number, output: number, cached?: number): TokenUsage {
  return {
    input,
    output,
    cached: cached ?? null,
    total: input + output
  };
}

export function createEmptyExecutionState(executionId: ExecutionID, diagramId?: DiagramID): ExecutionState {
  const now = new Date().toISOString();
  return {
    id: executionId,
    status: Status.PENDING,
    diagram_id: diagramId ?? null,
    started_at: now,
    ended_at: null,
    node_states: {},
    node_outputs: {},
    token_usage: { input: 0, output: 0, cached: null, total: 0 },
    error: null,
    variables: {},
    is_active: true,
    exec_counts: {},
    executed_nodes: []
  };
}

/**
 * Check if a status represents an active execution state
 */
export function isStatusActive(status: Status): boolean {
  return [
    Status.PENDING,
    Status.RUNNING,
    Status.PAUSED
  ].includes(status);
}

/**
 * Check if a status is valid for an execution context (excludes MAXITER_REACHED)
 */
export function isValidExecutionStatus(status: Status): boolean {
  return status !== Status.MAXITER_REACHED;
}

/**
 * Check if a status represents successful completion
 * For nodes, both COMPLETED and MAXITER_REACHED are considered successful
 */
export function isStatusSuccessful(status: Status, isNode: boolean = false): boolean {
  if (isNode) {
    return status === Status.COMPLETED || status === Status.MAXITER_REACHED;
  }
  return status === Status.COMPLETED;
}

/**
 * @deprecated Use isStatusActive instead
 */
export function isExecutionActive(status: Status): boolean {
  return isStatusActive(status);
}

/**
 * @deprecated Use isStatusActive instead
 */
export function isNodeExecutionActive(status: Status): boolean {
  return isStatusActive(status);
}

