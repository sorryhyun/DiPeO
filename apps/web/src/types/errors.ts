// types/errors.ts - Error classes

import type { Dict } from './primitives';

export class AgentDiagramError extends Error {
  constructor(message: string, readonly details?: Dict) {
    super(message);
    this.name = new.target.name;
  }
}

export class DependencyError extends AgentDiagramError {}
export class MaxIterationsError extends AgentDiagramError {}
export class ConditionEvaluationError extends AgentDiagramError {}

// Error handler factory
export function createErrorHandlerFactory(context: string) {
  return (error: unknown, details?: Dict) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[${context}] ${message}`, details);
    return new AgentDiagramError(`${context}: ${message}`, details);
  };
}