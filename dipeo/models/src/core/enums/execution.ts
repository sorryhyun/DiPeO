/**
 * Execution and event-related enumerations
 */

/**
 * Unified status enum for both executions and nodes
 * Note: MAXITER_REACHED only applies to node contexts
 */
export enum Status {
  PENDING = 'pending',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ABORTED = 'aborted',
  SKIPPED = 'skipped',
  MAXITER_REACHED = 'maxiter_reached'
}

/**
 * Flow control status for node execution
 */
export enum FlowStatus {
  WAITING = 'waiting',
  READY = 'ready',
  RUNNING = 'running',
  BLOCKED = 'blocked'
}

/**
 * Node execution completion status
 */
export enum CompletionStatus {
  SUCCESS = 'success',
  FAILED = 'failed',
  SKIPPED = 'skipped',
  MAX_ITER = 'max_iter'
}

/**
 * Execution phases for LLM and workflow operations
 */
export enum ExecutionPhase {
  MEMORY_SELECTION = 'memory_selection',
  DIRECT_EXECUTION = 'direct_execution',
  DECISION_EVALUATION = 'decision_evaluation',
  DEFAULT = 'default'
}


export enum EventType {
  // Execution lifecycle
  EXECUTION_STARTED = 'execution_started',
  EXECUTION_COMPLETED = 'execution_completed',
  EXECUTION_ERROR = 'execution_error',

  // Node lifecycle
  NODE_STARTED = 'node_started',
  NODE_COMPLETED = 'node_completed',
  NODE_ERROR = 'node_error',

  // Node output and logging
  NODE_OUTPUT = 'node_output',
  EXECUTION_LOG = 'execution_log',

  // Interactive
  INTERACTIVE_PROMPT = 'interactive_prompt',
  INTERACTIVE_RESPONSE = 'interactive_response'
}
