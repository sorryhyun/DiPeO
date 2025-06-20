/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import type { NodeID, DiagramID } from '../diagram';
import type { Message, MemoryState, MemoryConfig } from '../person';

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

export interface NodeResult {
  nodeId: NodeID;
  status: NodeExecutionStatus;
  output?: any;
  error?: string | null;
  timestamp: string; // ISO datetime string
  tokenUsage?: TokenUsage | null;
  skipReason?: string | null;
  progress?: string | null;
}

export interface ExecutionResult {
  executionId: ExecutionID;
  status: ExecutionStatus;
  results: NodeResult[];
  error?: string | null;
  metadata: Record<string, any>;
  totalTokenUsage?: TokenUsage | null;
}

export interface ExecutionState {
  id: ExecutionID;
  status: ExecutionStatus;
  diagramId?: DiagramID | null;
  startedAt: string; // ISO datetime string
  endedAt?: string | null; // ISO datetime string
  runningNodes: NodeID[];
  completedNodes: NodeID[];
  skippedNodes: NodeID[];
  pausedNodes: NodeID[];
  failedNodes: NodeID[];
  nodeOutputs: Record<string, any>;
  variables: Record<string, any>;
  tokenUsage?: TokenUsage | null;
  error?: string | null;
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

// Executor-specific types
export interface ExecutorResult {
  output?: any;
  error?: string | null;
  nodeId?: NodeID | null;
  executionTime?: number | null;
  tokenUsage?: TokenUsage | null;
  metadata?: Record<string, any>;
  validationErrors?: Array<Record<string, any>>;
}

// Specific node output types
export interface PersonJobOutput {
  output?: string | null;
  error?: string | null;
  conversationHistory?: PersonMemoryMessage[];
  tokenUsage?: TokenUsage | null;
  metadata?: Record<string, any>;
}

export interface ConditionOutput {
  result: boolean;
  evaluatedExpression: string;
  metadata?: Record<string, any>;
}

export interface JobOutput {
  output: any;
  error?: string | null;
  executionTime?: number;
  language?: string;
  metadata?: Record<string, any>;
}

// Execution context for handlers
export interface ExecutionContext {
  edges: Array<Record<string, any>>;
  results: Record<string, Record<string, any>>;
  currentNodeId: NodeID;
  executionId: string;
  execCnt?: Record<string, number>; // Node execution counts
  outputs?: Record<string, any>; // Node outputs
  persons?: Record<string, any>; // Person configurations
  apiKeys?: Record<string, string>; // API keys
}

// Node handler definition
export interface NodeDefinition {
  type: string;
  schema: any; // Type reference to schema class
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
    runningNodes: [],
    completedNodes: [],
    skippedNodes: [],
    pausedNodes: [],
    failedNodes: [],
    nodeOutputs: {},
    variables: {},
    tokenUsage: null,
    error: null,
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

