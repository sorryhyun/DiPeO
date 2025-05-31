// TypeScript types for execution engine and related structures
// These mirror the Python backend types for Phase 1 of the migration

import type { 
  Arrow,
  ArrowData,
  PersonDefinition 
} from './domain';

// ============================================================================
// Core Execution Types
// ============================================================================

export interface ExecutionContext {
  executionId: string;
  nodeOutputs: Record<string, any>;
  nodeExecutionCounts: Record<string, number>;
  totalCost: number;
  startTime: number;
  errors: Record<string, string>;
  executionOrder: string[];
  conditionValues: Record<string, boolean>;
  firstOnlyConsumed: Record<string, boolean>;
  diagram?: Record<string, any> | null;
  nodesById: Record<string, Record<string, any>>;
  outgoingArrows: Record<string, Record<string, any>[]>;
  incomingArrows: Record<string, Record<string, any>[]>;
}

export interface ExecutionMetadata {
  executionId: string;
  startTime: number;
  endTime?: number;
  totalCost: number;
  nodeCount: number;
  status: ExecutionStatus;
}

export type ExecutionStatus = 
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'paused';

export interface ExecutionResult {
  success: boolean;
  context: ExecutionContext;
  metadata: ExecutionMetadata;
  finalOutputs: Record<string, any>;
  errors: ExecutionError[];
}

export interface ExecutionOptions {
  streaming?: boolean;
  maxIterations?: number;
  timeout?: number;
  skipValidation?: boolean;
  debugMode?: boolean;
}

// ============================================================================
// Node and Diagram Types
// ============================================================================

export type NodeType = 
  | 'start'
  | 'person_job'
  | 'person_batch_job' 
  | 'condition'
  | 'db'
  | 'job'
  | 'endpoint';

export interface Position {
  x: number;
  y: number;
}

export interface NodeData {
  id: string;
  type: NodeType;
  label: string;
  [key: string]: any;
}

export interface Node {
  id: string;
  type: NodeType;
  position: Position;
  data: NodeData;
}


export interface Diagram {
  nodes: Node[];
  arrows: Arrow[];
  persons: PersonDefinition[];
  metadata?: DiagramMetadata;
}

export interface DiagramMetadata {
  id?: string;
  name?: string;
  description?: string;
  version?: string;
  createdAt?: number;
  updatedAt?: number;
}

// ============================================================================
// Enums and Constants
// ============================================================================

export enum ContentType {
  VARIABLE = 'variable',
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state'
}

export enum LLMService {
  OPENAI = 'openai',
  CLAUDE = 'claude',
  GEMINI = 'gemini',
  GROK = 'grok'
}

// ============================================================================
// Memory and Conversation Types
// ============================================================================

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata: Record<string, any>;
}

export interface PersonMemory {
  personId: string;
  messages: ConversationMessage[];
  context: Record<string, any>;
  lastUpdated: Date;
}


// ============================================================================
// LLM and Service Types
// ============================================================================

export interface ChatResult {
  text: string;
  usage?: any;
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
  rawResponse?: any;
}

export interface LLMUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cost: number;
}

export interface APIKeyInfo {
  id: string;
  name: string;
  service: LLMService;
  keyReference?: string;
  isValid?: boolean;
  lastUsed?: Date;
}

// ============================================================================
// Error Types
// ============================================================================

export interface ExecutionError {
  nodeId?: string;
  nodeType?: NodeType;
  message: string;
  details?: Record<string, any>;
  timestamp: Date;
  stack?: string;
}

export class AgentDiagramException extends Error {
  constructor(
    public message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'AgentDiagramException';
  }
}

export class ValidationError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'ValidationError';
  }
}

export class APIKeyError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'APIKeyError';
  }
}

export class LLMServiceError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'LLMServiceError';
  }
}

export class DiagramExecutionError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'DiagramExecutionError';
  }
}

export class NodeExecutionError extends AgentDiagramException {
  constructor(
    message: string,
    public nodeId: string,
    public nodeType: NodeType,
    details?: Record<string, any>
  ) {
    super(message, details);
    this.name = 'NodeExecutionError';
  }
}

export class DependencyError extends AgentDiagramException {
  constructor(
    message: string,
    public nodeId: string,
    public missingDependencies: string[],
    details?: Record<string, any>
  ) {
    super(message, details);
    this.name = 'DependencyError';
  }
}

export class MaxIterationsError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'MaxIterationsError';
  }
}

export class ConditionEvaluationError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'ConditionEvaluationError';
  }
}

export class PersonJobExecutionError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = 'PersonJobExecutionError';
  }
}

// ============================================================================
// Flow Control Types
// ============================================================================

export interface ArrowValidation {
  isValid: boolean;
  arrow: Arrow;
  reason?: string;
}

export interface DependencyInfo {
  nodeId: string;
  dependenciesMet: boolean;
  validArrows: Arrow[];
  missingDependencies: string[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ExecutionPlan {
  executionOrder: string[];
  parallelGroups: string[][];
  dependencies: Record<string, string[]>;
  estimatedCost: number;
  estimatedTime: number;
}

// ============================================================================
// Streaming Types
// ============================================================================

export interface StreamContext {
  executionId: string;
  outputFormat: 'sse' | 'websocket' | 'both';
  createdAt: Date;
}

export interface StreamUpdate {
  type: StreamUpdateType;
  executionId: string;
  nodeId?: string;
  data: any;
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

// ============================================================================
// Executor Types
// ============================================================================

export interface ExecutorResult {
  output: any;
  cost: number;
  metadata?: Record<string, any>;
}

export interface ExecutorValidation {
  isValid: boolean;
  errors: string[];
}

export interface BaseExecutorInterface {
  validateInputs(node: Node, context: ExecutionContext): Promise<ExecutorValidation>;
  execute(node: Node, context: ExecutionContext, options?: any): Promise<ExecutorResult>;
}

// ============================================================================
// Skip and Loop Control Types
// ============================================================================

export interface SkipManagerState {
  skipReasons: Record<string, string>;
  skippedNodes: Set<string>;
}

export interface LoopControllerState {
  maxIterations: number;
  loopNodes: string[];
  currentIteration: number;
  iterationCounts: Map<string, number>;
}

// ============================================================================
// Constants
// ============================================================================

export const DEFAULT_MAX_TOKENS = 4096;
export const DEFAULT_TEMPERATURE = 0.7;
export const DEFAULT_MAX_ITERATIONS = 100;
export const DEFAULT_EXECUTION_TIMEOUT = 300000; // 5 minutes

export const SUPPORTED_DOC_EXTENSIONS = new Set([
  '.txt', '.md', '.docx', '.pdf'
]);

export const SUPPORTED_CODE_EXTENSIONS = new Set([
  '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.jsx', '.tsx'
]);

export const COST_RATES: Record<string, { input: number; output: number }> = {
  openai: { input: 2.0, output: 8.0 },
  claude: { input: 3.0, output: 15.0 },
  gemini: { input: 1.0, output: 3.0 },
  grok: { input: 2.5, output: 10.0 }
};

// ============================================================================
// Type Guards
// ============================================================================

export function isExecutionError(error: any): error is ExecutionError {
  return error && typeof error.message === 'string' && error.timestamp instanceof Date;
}

export function isNodeExecutionError(error: any): error is NodeExecutionError {
  return error instanceof NodeExecutionError;
}

export function isValidNodeType(type: string): type is NodeType {
  return ['start', 'person_job', 'person_batch_job', 'condition', 'db', 'job', 'endpoint'].includes(type);
}

export function isValidExecutionStatus(status: string): status is ExecutionStatus {
  return ['pending', 'running', 'completed', 'failed', 'cancelled', 'paused'].includes(status);
}