// Import handle-related functions from domain/handle.ts to avoid duplication
import { createHandleId as handleIdImpl, isValidHandleIdFormat as isHandleIdImpl, parseHandleId as parseHandleIdImpl } from './domain/handle';

export type Brand<K, T> = K & { __brand: T };

export type NodeID = Brand<string, 'NodeID'>;
export type HandleID = Brand<string, 'HandleID'>;
export type ArrowID = Brand<string, 'ArrowID'>;
export type PersonID = Brand<string, 'PersonID'>;
export type ApiKeyID = Brand<string, 'ApiKeyID'>;
export type ExecutionID = Brand<string, 'ExecutionID'>;
export type MessageID = Brand<string, 'MessageID'>;


// Helper functions for creating branded types
export const nodeId = (id: string): NodeID => id as NodeID;
// handleId and parseHandleId are now re-exported from domain/handle.ts to avoid duplication
export const handleId = handleIdImpl;
export const parseHandleId = parseHandleIdImpl;
export const arrowId = (id: string): ArrowID => id as ArrowID;
export const personId = (id: string): PersonID => id as PersonID;
export const apiKeyId = (id: string): ApiKeyID => id as ApiKeyID;
export const executionId = (id: string): ExecutionID => id as ExecutionID;
export const messageId = (id: string): MessageID => id as MessageID;

// Type guards with proper validation
export const isNodeId = (id: string): id is NodeID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
// isHandleId is now re-exported from domain/handle.ts to avoid duplication
export const isHandleId = isHandleIdImpl;
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
