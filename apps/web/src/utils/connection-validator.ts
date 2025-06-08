// Connection validation utilities

import type { Handle, Node } from '@/types';
import { parseHandleId } from './canvas/handle-adapter';

export interface ConnectionRules {
  // Allow multiple connections to/from a handle
  allowMultiple?: boolean;
  // Type compatibility rules
  typeCompatibility?: 'strict' | 'loose' | 'any';
  // Custom validation function
  customValidator?: (from: Handle, to: Handle) => boolean;
}

const defaultRules: ConnectionRules = {
  allowMultiple: true,
  typeCompatibility: 'loose',
};

/**
 * Check if a connection can be made between two handles
 */
export function canConnect(
  fromHandleId: string,
  toHandleId: string,
  nodes: Map<string, Node>,
  existingArrows: Array<{ source: string; target: string }>,
  rules: ConnectionRules = defaultRules
): { valid: boolean; reason?: string } {
  // Parse handle IDs
  const { nodeId: fromNodeId } = parseHandleId(fromHandleId);
  const { nodeId: toNodeId } = parseHandleId(toHandleId);
  
  // Get nodes
  const fromNode = nodes.get(fromNodeId);
  const toNode = nodes.get(toNodeId);
  
  if (!fromNode || !toNode) {
    return { valid: false, reason: 'Node not found' };
  }
  
  // Get handles
  const fromHandle = fromNode.handles.find(h => h.id === fromHandleId);
  const toHandle = toNode.handles.find(h => h.id === toHandleId);
  
  if (!fromHandle || !toHandle) {
    return { valid: false, reason: 'Handle not found' };
  }
  
  // Check handle types (source -> target)
  if (fromHandle.kind !== 'source' || toHandle.kind !== 'target') {
    return { valid: false, reason: 'Invalid connection direction' };
  }
  
  // Check for self-connections (optional - some diagrams allow this)
  if (fromNodeId === toNodeId) {
    return { valid: false, reason: 'Cannot connect node to itself' };
  }
  
  // Check for duplicate connections
  const isDuplicate = existingArrows.some(
    arrow => arrow.source === fromHandleId && arrow.target === toHandleId
  );
  if (isDuplicate) {
    return { valid: false, reason: 'Connection already exists' };
  }
  
  // Check multiple connections rule
  if (!rules.allowMultiple) {
    const hasExistingTarget = existingArrows.some(arrow => arrow.target === toHandleId);
    if (hasExistingTarget) {
      return { valid: false, reason: 'Target handle already connected' };
    }
  }
  
  // Type compatibility check
  const typeCheck = checkTypeCompatibility(fromHandle, toHandle, rules.typeCompatibility || 'loose');
  if (!typeCheck.valid) {
    return typeCheck;
  }
  
  // Custom validation
  if (rules.customValidator) {
    const customResult = rules.customValidator(fromHandle, toHandle);
    if (!customResult) {
      return { valid: false, reason: 'Custom validation failed' };
    }
  }
  
  return { valid: true };
}

/**
 * Check type compatibility between handles
 */
function checkTypeCompatibility(
  from: Handle,
  to: Handle,
  mode: 'strict' | 'loose' | 'any'
): { valid: boolean; reason?: string } {
  if (mode === 'any') {
    return { valid: true };
  }
  
  const fromType = from.dataType || 'any';
  const toType = to.dataType || 'any';
  
  // Any type can connect to/from anything
  if (fromType === 'any' || toType === 'any') {
    return { valid: true };
  }
  
  if (mode === 'strict') {
    // Strict mode: types must match exactly
    if (fromType !== toType) {
      return { 
        valid: false, 
        reason: `Type mismatch: ${fromType} → ${toType}` 
      };
    }
  } else {
    // Loose mode: allow some type conversions
    const compatible = areTypesCompatible(fromType, toType);
    if (!compatible) {
      return { 
        valid: false, 
        reason: `Incompatible types: ${fromType} → ${toType}` 
      };
    }
  }
  
  return { valid: true };
}

/**
 * Check if two types are compatible in loose mode
 */
function areTypesCompatible(from: string, to: string): boolean {
  // Same type is always compatible
  if (from === to) return true;
  
  // Define compatibility rules
  const compatibilityMap: Record<string, string[]> = {
    'string': ['any'],
    'number': ['string', 'any'],
    'boolean': ['string', 'any'],
    'object': ['any'],
    'array': ['object', 'any'],
  };
  
  const compatibleTypes = compatibilityMap[from] || [];
  return compatibleTypes.includes(to);
}

/**
 * Get validation rules for specific node types
 */
export function getNodeConnectionRules(nodeType: string): ConnectionRules {
  switch (nodeType) {
    case 'condition':
      // Condition nodes have special rules
      return {
        allowMultiple: true,
        typeCompatibility: 'loose',
        customValidator: (from, to) => {
          // Only allow boolean outputs from condition nodes
          if (from.name === 'true' || from.name === 'false') {
            return true;
          }
          return false;
        },
      };
      
    case 'endpoint':
      // Endpoints can only have inputs
      return {
        allowMultiple: false,
        typeCompatibility: 'any',
      };
      
    case 'start':
      // Start nodes can only have outputs
      return {
        allowMultiple: true,
        typeCompatibility: 'any',
      };
      
    default:
      return defaultRules;
  }
}