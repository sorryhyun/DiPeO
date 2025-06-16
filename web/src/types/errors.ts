// types/errors.ts - Error classes

import type { Dict } from './utilities';

export class DiPeOError extends Error {
  constructor(message: string, readonly details?: Dict) {
    super(message);
    this.name = new.target.name;
  }
}

export class DependencyError extends DiPeOError {}
export class MaxIterationsError extends DiPeOError {}
export class ConditionEvaluationError extends DiPeOError {}

// Error handler factory
export function createErrorHandlerFactory(context: string) {
  return (error: unknown, details?: Dict) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[${context}] ${message}`, details);
    return new DiPeOError(`${context}: ${message}`, details);
  };
}