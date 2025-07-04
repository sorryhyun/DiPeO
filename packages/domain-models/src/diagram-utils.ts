/**
 * Utility functions for working with diagram domain models
 * These are TypeScript-only utilities not used in code generation
 */

import {
  DomainDiagram,
  DomainNode,
} from './diagram.js';

// Re-export handle utilities from conversions
export { parseHandleId, createHandleId, areHandlesCompatible } from './conversions.js';

// Utility function to create an empty diagram
export function createEmptyDiagram(): DomainDiagram {
  return {
    nodes: [],
    handles: [],
    arrows: [],
    persons: [],
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