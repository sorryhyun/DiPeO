/**
 * Shared execution domain models
 * These interfaces serve as the single source of truth for execution-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { z } from 'zod';
import type { NodeID, DiagramID, PersonID } from '../diagram';

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

// Person memory types
export interface PersonMemoryMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  tokenCount?: number;
}

export interface PersonMemoryState {
  personId: PersonID;
  messages: PersonMemoryMessage[];
  visibleMessages: number;
  hasMore?: boolean;
  config?: PersonMemoryConfig;
}

export interface PersonMemoryConfig {
  forgetMode?: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxMessages?: number;
  temperature?: number;
}

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

// Zod schemas for validation
export const ExecutionStatusSchema = z.nativeEnum(ExecutionStatus);
export const NodeExecutionStatusSchema = z.nativeEnum(NodeExecutionStatus);
export const EventTypeSchema = z.nativeEnum(EventType);

export const TokenUsageSchema = z.object({
  input: z.number(),
  output: z.number(),
  cached: z.number().nullable().optional(),
  total: z.number().optional()
});

export const NodeResultSchema = z.object({
  nodeId: z.string(),
  status: NodeExecutionStatusSchema,
  output: z.any().optional(),
  error: z.string().nullable().optional(),
  timestamp: z.string(),
  tokenUsage: TokenUsageSchema.nullable().optional(),
  skipReason: z.string().nullable().optional(),
  progress: z.string().nullable().optional()
});

export const ExecutionResultSchema = z.object({
  executionId: z.string(),
  status: ExecutionStatusSchema,
  results: z.array(NodeResultSchema),
  error: z.string().nullable().optional(),
  metadata: z.record(z.any()),
  totalTokenUsage: TokenUsageSchema.nullable().optional()
});

export const ExecutionStateSchema = z.object({
  id: z.string(),
  status: ExecutionStatusSchema,
  diagramId: z.string().nullable().optional(),
  startedAt: z.string(),
  endedAt: z.string().nullable().optional(),
  runningNodes: z.array(z.string()),
  completedNodes: z.array(z.string()),
  skippedNodes: z.array(z.string()),
  pausedNodes: z.array(z.string()),
  failedNodes: z.array(z.string()),
  nodeOutputs: z.record(z.any()),
  variables: z.record(z.any()),
  tokenUsage: TokenUsageSchema.nullable().optional(),
  error: z.string().nullable().optional(),
  durationSeconds: z.number().nullable().optional(),
  isActive: z.boolean().optional()
});

export const ExecutionEventSchema = z.object({
  executionId: z.string(),
  sequence: z.number(),
  eventType: EventTypeSchema,
  nodeId: z.string().nullable().optional(),
  timestamp: z.string(),
  data: z.record(z.any()),
  formattedMessage: z.string().optional()
});

export const ExecutionOptionsSchema = z.object({
  mode: z.enum(['normal', 'debug', 'monitor']).optional(),
  timeout: z.number().optional(),
  variables: z.record(z.any()).optional(),
  debug: z.boolean().optional()
});

export const InteractivePromptDataSchema = z.object({
  nodeId: z.string(),
  prompt: z.string(),
  timeout: z.number().optional(),
  defaultValue: z.string().nullable().optional()
});

export const PersonMemoryMessageSchema = z.object({
  id: z.string().optional(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  timestamp: z.string().optional(),
  tokenCount: z.number().optional()
});

export const PersonMemoryStateSchema = z.object({
  personId: z.string(),
  messages: z.array(PersonMemoryMessageSchema),
  visibleMessages: z.number(),
  hasMore: z.boolean().optional(),
  config: z.object({
    forgetMode: z.enum(['NO_FORGET', 'ON_EVERY_TURN', 'UPON_REQUEST']).optional(),
    maxMessages: z.number().optional(),
    temperature: z.number().optional()
  }).optional()
});

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
export function isTokenUsage(obj: unknown): obj is TokenUsage {
  return TokenUsageSchema.safeParse(obj).success;
}

export function isExecutionState(obj: unknown): obj is ExecutionState {
  return ExecutionStateSchema.safeParse(obj).success;
}

export function isExecutionEvent(obj: unknown): obj is ExecutionEvent {
  return ExecutionEventSchema.safeParse(obj).success;
}