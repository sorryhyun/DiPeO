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

// Note: Handle ID utility functions (parseHandleId, createHandleId) are now in utils/canvas/handle-adapter.ts
// They use the format "nodeId:handleName" as per the project's handle system

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