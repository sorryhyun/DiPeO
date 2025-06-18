import {
  NodeID,  HandleID,  ArrowID,  PersonID,  ApiKeyID,  DiagramID, ExecutionID,
  createHandleId as domainCreateHandleId,
  parseHandleId as domainParseHandleId
} from '@dipeo/domain-models';


export type Brand<K, T> = K & { __brand: T };

// Local branded type not in domain models
export type MessageID = Brand<string, 'MessageID'>;


// Helper functions for creating branded types
export const nodeId = (id: string): NodeID => id as NodeID;
export const handleId = (id: string): HandleID => id as HandleID;
export const arrowId = (id: string): ArrowID => id as ArrowID;
export const personId = (id: string): PersonID => id as PersonID;
export const apiKeyId = (id: string): ApiKeyID => id as ApiKeyID;
export const executionId = (id: string): ExecutionID => id as ExecutionID;
export const messageId = (id: string): MessageID => id as MessageID;
export const diagramId = (id: string): DiagramID => id as DiagramID;

// Handle ID utilities - use domain model functions
export const createHandleId = domainCreateHandleId;
export const parseHandleId = domainParseHandleId;

export const isValidHandleIdFormat = (id: string): boolean => {
  return id.includes(':') && id.split(':').length >= 2;
};

// Type guards with proper validation
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
