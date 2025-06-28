/**
 * Utility functions for working with diagram domain models
 * These are TypeScript-only utilities not used in code generation
 */

import {
  DomainDiagram,
  DomainNode,
  DomainHandle,
  NodeID,
  HandleID,
  HandleDirection,
  DataType
} from './diagram.js';

// Utility function to create an empty diagram
export function createEmptyDiagram(): DomainDiagram {
  return {
    nodes: [],
    handles: [],
    arrows: [],
    persons: [],
    apiKeys: [],
    metadata: {
      version: '2.0.0',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    }
  };
}

// Type guard for DomainNode
export function isDomainNode(obj: unknown): obj is DomainNode {
  // Simple type guard without Zod
  if (!obj || typeof obj !== 'object') return false;
  const node = obj as any;
  return (
    typeof node.id === 'string' &&
    typeof node.type === 'string' &&
    node.position &&
    typeof node.position.x === 'number' &&
    typeof node.position.y === 'number' &&
    node.data &&
    typeof node.data === 'object'
  );
}

// Handle utilities
export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  const [nodeId, ...handleNameParts] = handleId.split(':');
  return {
    nodeId: nodeId as NodeID,
    handleName: handleNameParts.join(':')
  };
}

export function createHandleId(nodeId: NodeID, handleName: string): HandleID {
  return `${nodeId}:${handleName}` as HandleID;
}

export function areHandlesCompatible(source: DomainHandle, target: DomainHandle): boolean {
  // Basic compatibility: output can connect to input
  if (source.direction !== HandleDirection.OUTPUT || target.direction !== HandleDirection.INPUT) {
    return false;
  }
  
  // Type compatibility
  if (source.dataType === DataType.ANY || target.dataType === DataType.ANY) {
    return true;
  }
  
  return source.dataType === target.dataType;
}