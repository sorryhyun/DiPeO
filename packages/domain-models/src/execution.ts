/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import type { NodeID, DiagramID, MemoryConfig } from './diagram.js';
import type { Message, MemoryState } from './conversation.js';

// Type aliases
export type ExecutionID = string & { readonly __brand: 'ExecutionID' };

// Enums - unified status values for consistency
export enum ExecutionStatus {
  PENDING = 'PENDING',      // Unified with NodeExecutionStatus
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  ABORTED = 'ABORTED',
  SKIPPED = 'SKIPPED'       // Added for consistency
}

export enum NodeExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  ABORTED = 'ABORTED',      // Added for consistency
  SKIPPED = 'SKIPPED'
}

export enum EventType {
  // Core execution lifecycle events
  EXECUTION_STATUS_CHANGED = 'EXECUTION_STATUS_CHANGED',
  NODE_STATUS_CHANGED = 'NODE_STATUS_CHANGED',
  
  // Progress and interaction events
  NODE_PROGRESS = 'NODE_PROGRESS',
  INTERACTIVE_PROMPT = 'INTERACTIVE_PROMPT',
  INTERACTIVE_RESPONSE = 'INTERACTIVE_RESPONSE',
  
  // Error handling
  EXECUTION_ERROR = 'EXECUTION_ERROR',
  
  // Generic update event
  EXECUTION_UPDATE = 'EXECUTION_UPDATE'
}

// Core models
export interface TokenUsage {
  input: number;
  output: number;
  cached?: number | null;
  total?: number; // Computed field
}

// Simplified node state tracking
export interface NodeState {
  status: NodeExecutionStatus;
  started_at?: string | null;
  ended_at?: string | null;
  error?: string | null;
  token_usage?: TokenUsage | null;
}

// Single output format for ALL nodes
export interface NodeOutput {
  value: any;  // The actual output
  metadata?: Record<string, any>;  // Flexible metadata
}

// Simplified execution state
export interface ExecutionState {
  id: ExecutionID;
  status: ExecutionStatus;
  diagram_id?: DiagramID | null;
  started_at: string;
  ended_at?: string | null;
  // Simplified node tracking
  node_states: Record<string, NodeState>;
  node_outputs: Record<string, NodeOutput>;
  token_usage: TokenUsage;
  error?: string | null;
  variables: Record<string, any>;
  duration_seconds?: number | null; // Computed field
  is_active?: boolean; // Computed field
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

// Use shared conversation types from person domain
export type PersonMemoryMessage = Message;
export type PersonMemoryState = MemoryState;
export type PersonMemoryConfig = MemoryConfig;

// Update events for real-time communication
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


// Node handler definition
export interface NodeDefinition {
  type: string;
  node_schema: any; // Type reference to schema class (renamed from 'schema' to avoid Pydantic conflict)
  handler: any; // Handler function reference
  requires_services?: string[];
  description?: string;
}


// Utility functions
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
    is_active: true
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

// Type guards