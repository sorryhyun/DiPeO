// Import and re-export branded types from domain models
import type {
  NodeID,
  HandleID,
  ArrowID,
  PersonID,
  ApiKeyID,
  DiagramID,
  ExecutionID
} from '@dipeo/domain-models';

export type {
  NodeID,
  HandleID,
  ArrowID,
  PersonID,
  ApiKeyID,
  DiagramID,
  ExecutionID
};

// Re-export handle utilities from domain models
export {
  createHandleId,
  parseHandleId
} from '@dipeo/domain-models';

// Generic brand type utility
export type Brand<K, T> = K & { __brand: T };

// UI-specific branded type not in domain models
export type MessageID = Brand<string, 'MessageID'>;


// UI-specific helper functions for creating branded IDs
// Note: These are not exported from domain-models as they're implementation details
export const nodeId = (id: string): NodeID => id as NodeID;
export const handleId = (id: string): HandleID => id as HandleID;
export const arrowId = (id: string): ArrowID => id as ArrowID;
export const personId = (id: string): PersonID => id as PersonID;
export const apiKeyId = (id: string): ApiKeyID => id as ApiKeyID;
export const executionId = (id: string): ExecutionID => id as ExecutionID;
export const messageId = (id: string): MessageID => id as MessageID;
export const diagramId = (id: string): DiagramID => id as DiagramID;

// Additional handle validation not provided by domain models
export const isValidHandleIdFormat = (id: string): boolean => {
  return id.includes('_') && id.split('_').length >= 2;
};

// UI-specific type guards with validation
// Note: These validation rules are specific to the frontend implementation
export const isNodeId = (id: string): id is NodeID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
export const isHandleId = (id: string): id is HandleID => {
  return isValidHandleIdFormat(id);
};
export const isArrowId = (id: string): id is ArrowID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
export const isPersonId = (id: string): id is PersonID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
export const isApiKeyId = (id: string): id is ApiKeyID => {
  return /^APIKEY_[a-zA-Z0-9]+$/.test(id);
};
export const isExecutionId = (id: string): id is ExecutionID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
export const isMessageId = (id: string): id is MessageID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
export const isDiagramId = (id: string): id is DiagramID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
