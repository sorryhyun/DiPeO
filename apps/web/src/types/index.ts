// types/config.ts - Central export point for all types

// Re-export all types from separate modules
export * from './primitives';
export * from './api';
export * from './runtime';
export * from './errors';
export * from './domain';
export * from './framework';
export * from './ui';
export * from './config';
export * from './validation';

// Re-export branded types
export type { 
  Brand,
  NodeID,
  HandleID,
  ArrowID,
  PersonID,
  ApiKeyID,
  ExecutionID,
  MessageID
} from './branded';

export {
  nodeId,
  handleId,
  arrowId,
  personId,
  apiKeyId,
  executionId,
  messageId,
  isNodeId,
  isHandleId,
  isArrowId,
  isPersonId,
  isApiKeyId,
  isExecutionId,
  isMessageId,
} from './branded';

// Legacy exports for backward compatibility


// Export type guards
export * from './typeGuardsRefactored';

// Type guard factory types (for advanced usage)
export type { TypeGuard, TypeGuardConfig, PropertyCheck } from '@/utils/typeGuardFactory';