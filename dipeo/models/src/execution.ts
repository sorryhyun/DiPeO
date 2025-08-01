/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import type { NodeID, DiagramID } from './diagram.js';
import type { Message } from './conversation.js';
import { ExecutionStatus, NodeExecutionStatus, EventType } from './enums.js';

export type ExecutionID = string & { readonly __brand: 'ExecutionID' };

export { ExecutionStatus, NodeExecutionStatus, EventType };

export interface TokenUsage {
  input: number;
  output: number;
  cached?: number | null;
  total?: number;
}

export interface NodeState {
  status: NodeExecutionStatus;
  started_at?: string | null;
  ended_at?: string | null;
  error?: string | null;
  token_usage?: TokenUsage | null;
  output?: Record<string, any> | null;
}


export interface ExecutionState {
  id: ExecutionID;
  status: ExecutionStatus;
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
  status?: NodeExecutionStatus;
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
    status: ExecutionStatus.PENDING,
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

export function isExecutionActive(status: ExecutionStatus): boolean {
  return [
    ExecutionStatus.PENDING,
    ExecutionStatus.RUNNING,
    ExecutionStatus.PAUSED
  ].includes(status);
}

export function isNodeExecutionActive(status: NodeExecutionStatus): boolean {
  return [
    NodeExecutionStatus.PENDING,
    NodeExecutionStatus.RUNNING,
    NodeExecutionStatus.PAUSED
  ].includes(status);
}

