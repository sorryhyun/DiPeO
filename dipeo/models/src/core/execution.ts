/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import type { NodeID, DiagramID } from './diagram.js';
import type { Message } from './conversation.js';
import { Status, EventType } from './enums/execution.js';
import { JsonValue, JsonDict } from './types/json.js';

export type ExecutionID = string & { readonly __brand: 'ExecutionID' };

export { Status, EventType };

export interface LLMUsage {
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
  llm_usage?: LLMUsage | null;
  output?: Record<string, any> | null;
}

export interface NodeMetrics {
  node_id: string;
  node_type: string;
  start_time: number;
  end_time?: number | null;
  duration_ms?: number | null;
  memory_usage?: number | null;
  llm_usage?: LLMUsage | null;
  error?: string | null;
  dependencies?: string[];
}

export interface Bottleneck {
  node_id: string;
  node_type: string;
  duration_ms: number;
  percentage: number;
}

export interface ExecutionMetrics {
  execution_id: ExecutionID;
  start_time: number;
  end_time?: number | null;
  total_duration_ms?: number | null;
  node_metrics: Record<string, NodeMetrics>;
  critical_path?: string[];
  parallelizable_groups?: string[][];
  bottlenecks?: Bottleneck[];
}


// Envelope metadata structure
export interface EnvelopeMeta {
  node_id?: string;
  llm_usage?: LLMUsage;
  execution_time?: number;
  retry_count?: number;
  error?: string;
  error_type?: string;
  timestamp?: string | number;
  // Other potential metadata fields
  [key: string]: any;
}

// Serialized Envelope format (new)
export interface SerializedEnvelope {
  envelope_format: true;  // Discriminator field
  id: string;
  trace_id: string;
  produced_by: string;
  content_type: string;
  schema_id?: string;
  serialization_format?: string;
  body: any;
  meta: EnvelopeMeta;
  representations?: Record<string, any>;  // Multiple representations of the output
}

// SerializedNodeOutput is now just SerializedEnvelope
// Legacy format support has been removed
export type SerializedNodeOutput = SerializedEnvelope;

export interface ExecutionState {
  id: ExecutionID;
  status: Status;
  diagram_id?: DiagramID | null;
  started_at: string;
  ended_at?: string | null;
  node_states: Record<string, NodeState>;
  node_outputs: Record<string, SerializedNodeOutput>;
  llm_usage: LLMUsage;
  error?: string | null;
  variables?: JsonDict;
  metadata?: JsonDict;
  duration_seconds?: number | null;
  is_active?: boolean;
  exec_counts: Record<string, number>;
  executed_nodes: string[];
  metrics?: ExecutionMetrics | null;
}



export interface ExecutionOptions {
  mode?: 'normal' | 'debug' | 'monitor';
  timeout?: number;
  variables?: JsonDict;
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
  result?: JsonValue;
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


export function createLLMUsage(input: number, output: number, cached?: number): LLMUsage {
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
    llm_usage: { input: 0, output: 0, cached: null, total: 0 },
    error: null,
    variables: {},
    metadata: {},
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

