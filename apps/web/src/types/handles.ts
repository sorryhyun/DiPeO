// Handle system type definitions

import type { ID } from './primitives';

// Data types for type-safe connections
export type DataType = 
  | 'any'
  | 'string'
  | 'number' 
  | 'boolean'
  | 'object'
  | 'array'
  | { custom: string };

// Enhanced handle definition
export interface HandleDef {
  id: string;
  kind: 'input' | 'output';
  position: 'top' | 'right' | 'bottom' | 'left';
  dataType?: DataType;
  required?: boolean;
  multiple?: boolean;
  label?: string;
  offset?: { x: number; y: number };
  color?: string;
}

// Connection validation rules
export interface ConnectionRules {
  canConnect(from: HandleDef, to: HandleDef): boolean;
}

// Handle-based arrow (future)
export interface HandleArrow {
  id: ID;
  from: ID;  // Handle ID
  to: ID;    // Handle ID
  data?: Record<string, any>;
}

// Utility functions for handle IDs
export function parseHandleId(handleId: string): { nodeId: string; type: string; name: string } | null {
  const parts = handleId.split('-');
  if (parts.length < 3) return null;
  
  // Handle IDs are in format: nodeId-type-name
  // nodeId might contain dashes, so we need to handle that
  const type = parts[parts.length - 2];
  const name = parts[parts.length - 1];
  const nodeId = parts.slice(0, -2).join('-');
  
  return { nodeId, type, name };
}

export function createHandleId(nodeId: string, type: 'input' | 'output', name: string): string {
  return `${nodeId}-${type}-${name}`;
}

// Type compatibility checking
export function areTypesCompatible(from: DataType | undefined, to: DataType | undefined): boolean {
  // No type info means compatible
  if (!from || !to) return true;
  
  // 'any' is compatible with everything
  if (from === 'any' || to === 'any') return true;
  
  // Direct match
  if (from === to) return true;
  
  // Custom type matching
  if (typeof from === 'object' && typeof to === 'object') {
    return from.custom === to.custom;
  }
  
  return false;
}

// Default connection rules implementation
export const defaultConnectionRules: ConnectionRules = {
  canConnect(from: HandleDef, to: HandleDef): boolean {
    // Basic checks
    if (from.kind !== 'output' || to.kind !== 'input') return false;
    
    // Type compatibility
    return areTypesCompatible(from.dataType, to.dataType);
  }
};