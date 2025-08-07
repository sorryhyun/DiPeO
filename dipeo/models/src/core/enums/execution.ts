/**
 * Execution and event-related enumerations
 */

/**
 * Unified status enum for both executions and nodes
 * Note: MAXITER_REACHED only applies to node contexts
 */
export enum Status {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  ABORTED = 'ABORTED',
  SKIPPED = 'SKIPPED',
  MAXITER_REACHED = 'MAXITER_REACHED'
}

/**
 * @deprecated Use Status instead
 */
export type ExecutionStatus = Status;

/**
 * @deprecated Use Status instead
 */
export type NodeExecutionStatus = Status;

export enum EventType {
  EXECUTION_STATUS_CHANGED = 'EXECUTION_STATUS_CHANGED',
  NODE_STATUS_CHANGED = 'NODE_STATUS_CHANGED',
  NODE_PROGRESS = 'NODE_PROGRESS',
  INTERACTIVE_PROMPT = 'INTERACTIVE_PROMPT',
  INTERACTIVE_RESPONSE = 'INTERACTIVE_RESPONSE',
  EXECUTION_ERROR = 'EXECUTION_ERROR',
  EXECUTION_UPDATE = 'EXECUTION_UPDATE',
  EXECUTION_LOG = 'EXECUTION_LOG'
}