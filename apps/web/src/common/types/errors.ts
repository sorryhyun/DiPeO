// Error types
import { NodeType } from './node';

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