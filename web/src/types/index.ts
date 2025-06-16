// types/config.ts - Central export point for all types

// Core types - single source of truth
export * from './core';

// Re-export all types from separate modules
export * from './primitives';
export * from './runtime';
export * from './errors';
export * from './framework';
export * from './ui';
export * from './config';

// Re-export branded types
export type { 
  Brand,
  NodeID,
  HandleID,
  ArrowID,
  PersonID,
  ApiKeyID,
  ExecutionID,
  MessageID,
  DiagramID
} from './branded';

export {
  nodeId,
  handleId,
  arrowId,
  personId,
  apiKeyId,
  executionId,
  messageId,
  diagramId,
  isNodeId,
  isHandleId,
  isArrowId,
  isPersonId,
  isApiKeyId,
  isExecutionId,
  isMessageId,
  isDiagramId,
  createHandleId,
  parseHandleId,
} from './branded';

// Legacy exports for backward compatibility

// Type guard factory types removed - file doesn't exist

// GraphQL type mappings and domain compatibility
export * from './graphql-mappings';
export type {
  Node,
  Arrow,
  Handle,
  Person,
  ApiKey,
  Diagram,
  ExecutionStatus,
  EventType
} from '@/__generated__/graphql';

// Export enums as both types and values
export {
  NodeType,
  LlmService,
  ForgettingMode
} from '@/__generated__/graphql';