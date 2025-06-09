/**
 * Centralized definitions for the type system
 */

export type NodeKind = 'start' | 'condition' | 'person_job' | 'endpoint' | 'db' |
    'job' | 'user_response' | 'notion' | 'person_batch_job';

export type DataType = 'any' | 'string' | 'number' | 'boolean' | 'array' | 'object' |
    'text' | 'integer' | 'float' | 'json';

export type ArrowKind = 'default' | 'straight' | 'step' | 'smoothstep' | 'bezier';

export type HandlePosition = 'top' | 'right' | 'bottom' | 'left';

export type NodeExecutionState = 'pending' | 'running' | 'completed' | 'failed' | 
    'skipped' | 'paused';

export type ConnectionMode = 'strict' | 'loose';

export type PersonForgettingStrategy = 'no_forget' | 'on_every_turn' | 'upon_request';

export type PersonService = 'openai' | 'claude' | 'gemini' | 'grok' | 'custom';

export type JobLanguage = 'python' | 'javascript' | 'bash';

export type DBOperation = 'save' | 'load' | 'delete' | 'update' | 'query';

export type NotionOperation = 'read' | 'write';

export type ConditionType = 'expression' | 'detect_max_iterations';

export type DBSubType = 'fixed_prompt' | 'file';

export type ProcessType = 'batch' | 'sequential';