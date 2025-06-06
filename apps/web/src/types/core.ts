// Core domain types - Essential entities and their relationships

export interface Node {
  id: string;
  type: 'start' | 'job' | 'person_job' | 'condition' | 'endpoint' | 'db' | 'notion' | 'person_batch_job' | 'user_response';
  position: { x: number; y: number };
  data: Record<string, any>; // Flexible data storage - stop over-typing
}

export interface Arrow {
  id: string;
  source: string;
  target: string;
  type?: string;
  sourceHandle?: string;
  targetHandle?: string;
  data?: Record<string, any>;
}

export interface Person {
  id: string;
  label: string;
  apiKeyId?: string;
  modelName?: string;
  service?: string;
  systemPrompt?: string;
  memory?: ConversationMessage[];
  options?: Record<string, any>;
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  service: 'openai' | 'anthropic' | 'google' | 'notion' | 'grok'  | 'custom';
}

export interface Diagram {
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
  metadata?: {
    id?: string;
    name?: string;
    description?: string;
    created?: string;
    modified?: string;
  };
}

// API types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  filename?: string;
  path?: string;
}

export interface ChatResult {
  text: string;
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}

// Validation types
export interface ArrowValidation {
  isValid: boolean;
  arrow: Arrow;
  reason?: string;
}

export interface DependencyInfo {
  node_id: string;
  dependenciesMet: boolean;
  validArrows: Arrow[];
  missingDependencies: string[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// Error types
export type NodeType = Node['type'];

export class AgentDiagramException extends Error {
  constructor(
    public message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AgentDiagramException';
  }
}

export class ValidationError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'ValidationError';
  }
}

export class APIKeyError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'APIKeyError';
  }
}

export class LLMServiceError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'LLMServiceError';
  }
}

export class DiagramExecutionError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'DiagramExecutionError';
  }
}

export class NodeExecutionError extends AgentDiagramException {
  constructor(
    message: string,
    public nodeId: string,
    public nodeType: NodeType,
    details?: Record<string, unknown>
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
    details?: Record<string, unknown>
  ) {
    super(message, details);
    this.name = 'DependencyError';
  }
}

export class MaxIterationsError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'MaxIterationsError';
  }
}

export class ConditionEvaluationError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'ConditionEvaluationError';
  }
}

export class PersonJobExecutionError extends AgentDiagramException {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = 'PersonJobExecutionError';
  }
}

// Error handler factory
export function createErrorHandlerFactory(context: string) {
  return (error: unknown): void => {
    console.error(`[${context}] Error:`, error);
    if (error instanceof Error) {
      console.error(`[${context}] Stack:`, error.stack);
    }
  };
}

// Type aliases for compatibility
export type DiagramNode = Node;
export type DiagramState = Diagram;
export type PersonDefinition = Person;
export type ArrowData = Record<string, any>;
export type DiagramNodeData = Record<string, any>;