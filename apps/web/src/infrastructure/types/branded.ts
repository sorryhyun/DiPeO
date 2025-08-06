/**
 * UI-specific branded types and utilities
 * Domain branded types are imported from './domain'
 */

import { 
  parseHandleId as domainParseHandleId,
  type NodeID,
  type HandleID,
  type ArrowID,
  type PersonID,
  type ApiKeyID,
  type ExecutionID,
  type DiagramID
} from './domain';

// Re-export all branded types and utilities from domain
export {
  // Branded types
  type NodeID,
  type HandleID,
  type ArrowID,
  type PersonID,
  type ApiKeyID,
  type DiagramID,
  type ExecutionID,
  // ID creation functions
  nodeId,
  handleId,
  arrowId,
  personId,
  apiKeyId,
  diagramId,
  executionId,
  // Handle utilities
  createHandleId,
  parseHandleId,
  HandleDirection
} from './domain';

// Generic brand type utility for UI-specific types
export type Brand<K, T> = K & { __brand: T };

// UI-specific branded type not in domain models
export type MessageID = Brand<string, 'MessageID'>;

// UI-specific ID creation function
export const messageId = (id: string): MessageID => id as MessageID;

// Handle validation using domain utility
export const isValidHandleIdFormat = (id: string): boolean => {
  try {
    const parsed = domainParseHandleId(id as HandleID);
    return parsed !== null && 
           'nodeId' in parsed && 
           'label' in parsed && 
           'direction' in parsed;
  } catch {
    return false;
  }
};

// UI-specific type guards for branded IDs
// These provide runtime validation for ID formats
export const isNodeId = (id: unknown): id is NodeID => {
  return typeof id === 'string' && /^[a-zA-Z0-9_-]+$/.test(id);
};

export const isHandleId = (id: unknown): id is HandleID => {
  return typeof id === 'string' && isValidHandleIdFormat(id);
};

export const isArrowId = (id: unknown): id is ArrowID => {
  return typeof id === 'string' && /^[a-zA-Z0-9_-]+$/.test(id);
};

export const isPersonId = (id: unknown): id is PersonID => {
  return typeof id === 'string' && /^[a-zA-Z0-9_-]+$/.test(id);
};

export const isApiKeyId = (id: unknown): id is ApiKeyID => {
  return typeof id === 'string' && /^APIKEY_[a-zA-Z0-9]+$/.test(id);
};

export const isExecutionId = (id: unknown): id is ExecutionID => {
  return typeof id === 'string' && /^[a-zA-Z0-9_-]+$/.test(id);
};

export const isMessageId = (id: unknown): id is MessageID => {
  return typeof id === 'string' && /^[a-zA-Z0-9_-]+$/.test(id);
};

export const isDiagramId = (id: unknown): id is DiagramID => {
  return typeof id === 'string' && /^[a-zA-Z0-9_-]+$/.test(id);
};
