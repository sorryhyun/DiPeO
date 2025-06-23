/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import type { NodeID, DiagramID } from './diagram.js';
import type { Message, MemoryState, MemoryConfig } from './person.js';

// Type aliases
export type ExecutionID = string & { readonly __brand: 'ExecutionID' };

// Enums
export enum ExecutionStatus {
  STARTED = 'STARTED',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  ABORTED = 'ABORTED'
}

export enum NodeExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  SKIPPED = 'SKIPPED',
  PAUSED = 'PAUSED'
}

export enum EventType {
  EXECUTION_STARTED = 'EXECUTION_STARTED',
  NODE_STARTED = 'NODE_STARTED',
  NODE_RUNNING = 'NODE_RUNNING',
  NODE_COMPLETED = 'NODE_COMPLETED',
  NODE_FAILED = 'NODE_FAILED',
  NODE_SKIPPED = 'NODE_SKIPPED',
  NODE_PAUSED = 'NODE_PAUSED',
  NODE_PROGRESS = 'NODE_PROGRESS',
  EXECUTION_COMPLETED = 'EXECUTION_COMPLETED',
  EXECUTION_FAILED = 'EXECUTION_FAILED',
  EXECUTION_ABORTED = 'EXECUTION_ABORTED',
  INTERACTIVE_PROMPT = 'INTERACTIVE_PROMPT',
  INTERACTIVE_RESPONSE = 'INTERACTIVE_RESPONSE',
  EXECUTION_ERROR = 'EXECUTION_ERROR',
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
  startedAt?: string | null;
  endedAt?: string | null;
  error?: string | null;
  skipReason?: string | null;
  tokenUsage?: TokenUsage | null;
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
  diagramId?: DiagramID | null;
  startedAt: string;
  endedAt?: string | null;
  // Simplified node tracking
  nodeStates: Record<string, NodeState>;
  nodeOutputs: Record<string, NodeOutput>;
  tokenUsage: TokenUsage;
  error?: string | null;
  variables: Record<string, any>;
  durationSeconds?: number | null; // Computed field
  isActive?: boolean; // Computed field
}


export interface ExecutionEvent {
  executionId: ExecutionID;
  sequence: number;
  eventType: EventType;
  nodeId?: NodeID | null;
  timestamp: string; // ISO datetime string
  data: Record<string, any>;
  formattedMessage?: string; // Computed field
}

export interface ExecutionOptions {
  mode?: 'normal' | 'debug' | 'monitor';
  timeout?: number;
  variables?: Record<string, any>;
  debug?: boolean;
}

export interface InteractivePromptData {
  nodeId: NodeID;
  prompt: string;
  timeout?: number;
  defaultValue?: string | null;
}

export interface InteractiveResponse {
  nodeId: NodeID;
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
  executionId: ExecutionID;
  nodeId?: NodeID;
  status?: NodeExecutionStatus;
  result?: any;
  error?: string;
  timestamp?: string;
  totalTokens?: number;
  nodeType?: string;
  tokens?: number;
  data?: Record<string, any>;
}

// Simplified execution context (data only, no services)
export interface ExecutionContext {
  executionId: ExecutionID;
  diagramId: DiagramID;
  nodeStates: Record<string, NodeState>;
  nodeOutputs: Record<string, any>;
  variables: Record<string, any>;
}

// Node handler definition
export interface NodeDefinition {
  type: string;
  nodeSchema: any; // Type reference to schema class (renamed from 'schema' to avoid Pydantic conflict)
  handler: any; // Handler function reference
  requiresServices?: string[];
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
    status: ExecutionStatus.STARTED,
    diagramId: diagramId ?? null,
    startedAt: now,
    endedAt: null,
    nodeStates: {},
    nodeOutputs: {},
    tokenUsage: { input: 0, output: 0, cached: null, total: 0 },
    error: null,
    variables: {},
    isActive: true
  };
}

export function isExecutionActive(status: ExecutionStatus): boolean {
  return [
    ExecutionStatus.STARTED,
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