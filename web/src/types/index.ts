// types/config.ts - Central export point for all types

// Core types - single source of truth
export * from './core';

// Re-export all types from separate modules
export * from './runtime';
export * from './errors';
export * from './ui';
export * from './config';

// Export React Flow types and adapters from DiagramAdapter
export type {
  ReactFlowDiagram,
  DiPeoNode,
  DiPeoEdge,
  ValidatedConnection,
  DiPeoReactInstance
} from '@/adapters/DiagramAdapter';

export {
  isDiPeoNode,
  isDiPeoEdge,
  nodeToReact,
  arrowToReact,
  diagramToReact,
  reactToNode,
  reactToArrow,
  connectionToArrow,
  validateConnection,
  DiagramAdapter
} from '@/adapters/DiagramAdapter';

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

export * from './utilities'

export type {NodeKind, NODE_KINDS} from './generated/node-kinds';
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