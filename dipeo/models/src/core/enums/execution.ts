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
  EXECUTION_STATUS_CHANGED = 'execution_status_changed',

  // Node lifecycle
  NODE_STARTED = 'node_started',
  NODE_COMPLETED = 'node_completed',
  NODE_ERROR = 'node_error',
  NODE_OUTPUT = 'node_output',
  NODE_STATUS_CHANGED = 'node_status_changed',
  NODE_PROGRESS = 'node_progress',

  // Metrics and monitoring
  METRICS_COLLECTED = 'metrics_collected',
  OPTIMIZATION_SUGGESTED = 'optimization_suggested',

  // External integrations
  WEBHOOK_RECEIVED = 'webhook_received',

  // Interactive
  INTERACTIVE_PROMPT = 'interactive_prompt',
  INTERACTIVE_RESPONSE = 'interactive_response',

  // Logging and updates
  EXECUTION_UPDATE = 'execution_update',
  EXECUTION_LOG = 'execution_log',

  // WebSocket maintenance
  KEEPALIVE = 'keepalive'
}
