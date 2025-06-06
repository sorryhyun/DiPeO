// Core type exports
export * from './core';
export * from './runtime';
export * from './ui';

// Type aliases for backward compatibility during migration
export type { Node as DiagramNode } from './core';
export type { Diagram as DiagramState } from './core';
export type { Person as PersonDefinition } from './core';
export type ArrowData = Record<string, any>;
export type DiagramNodeData = Record<string, any>;

// Legacy BlockData types (all mapped to Record<string, any>)
export type StartBlockData = Record<string, any>;
export type JobBlockData = Record<string, any>;
export type PersonJobBlockData = Record<string, any>;
export type ConditionBlockData = Record<string, any>;
export type EndpointBlockData = Record<string, any>;
export type DBBlockData = Record<string, any>;
export type NotionBlockData = Record<string, any>;
export type PersonBatchJobBlockData = Record<string, any>;
export type UserResponseBlockData = Record<string, any>;

// Explicit exports from properties
export {
  type FormFieldProps,
  type PanelProps
} from './properties';

// Explicit exports from api
export * from './api';

// Explicit exports from errors
export {
  AgentDiagramException,
  ValidationError,
  APIKeyError,
  LLMServiceError,
  DiagramExecutionError,
  NodeExecutionError,
  DependencyError,
  MaxIterationsError,
  ConditionEvaluationError,
  PersonJobExecutionError,
  createErrorHandlerFactory
} from './errors';

// Explicit exports from validation
export {
  type ArrowValidation,
  type DependencyInfo,
  type ValidationResult
} from './validation';

// Missing exports
export { UNIFIED_NODE_CONFIGS, getNodeConfig, getReactFlowType } from './nodeConfig';