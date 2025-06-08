export type Brand<K, T> = K & { __brand: T };

export type NodeID = Brand<string, 'NodeID'>;
export type HandleID = Brand<string, 'HandleID'>;
export type ArrowID = Brand<string, 'ArrowID'>;
export type PersonID = Brand<string, 'PersonID'>;
export type ApiKeyID = Brand<string, 'ApiKeyID'>;


// Helper functions for creating branded types
export const nodeId = (id: string): NodeID => id as NodeID;
export const handleId = (nodeId: NodeID, handleName: string): HandleID => 
  `${nodeId}:${handleName}` as HandleID;
export const arrowId = (id: string): ArrowID => id as ArrowID;
export const personId = (id: string): PersonID => id as PersonID;
export const apiKeyId = (id: string): ApiKeyID => id as ApiKeyID;

// Type guards with proper validation
export const isNodeId = (id: string): id is NodeID => {
  return /^[a-zA-Z0-9_-]+$/.test(id);
};
export const isHandleId = (id: string): id is HandleID => {
  return /^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$/.test(id);
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

// Parse handle ID to extract node ID and handle name
export const parseHandleId = (id: HandleID): { nodeId: NodeID; handleName: string } => {
  const parts = (id as string).split(':');
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    throw new Error(`Invalid handle ID format: ${id}`);
  }
  return { nodeId: nodeId(parts[0]), handleName: parts[1] };
};