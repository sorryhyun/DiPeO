// Connection validation utilities

import type { Handle, Node } from '@/types';
import { parseHandleId } from './canvas/handle-adapter';
import { 
  validateConnection as validateTypedConnection, 
  findValidTargets as findTypedValidTargets, 
  findValidSources as findTypedValidSources,
  areDataTypesCompatible
} from './connections/typed-connection';
import type { Arrow } from '@/types/arrow';
import type { HandleID } from '@/types/branded';

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
  
  // Use the typed system's compatibility checker if possible
  try {
    return areDataTypesCompatible(from as any, to as any);
  } catch {
    // Fallback to legacy compatibility rules
    const compatibilityMap: Record<string, string[]> = {
      'string': ['any', 'text'],
      'number': ['string', 'any', 'float', 'integer'],
      'boolean': ['string', 'any'],
      'object': ['any', 'json'],
      'array': ['object', 'any'],
    };
    
    const compatibleTypes = compatibilityMap[from] || [];
    return compatibleTypes.includes(to);
  }
}

/**
 * Validate connection using the new typed system
 * This is a wrapper to integrate with the legacy system
 */
export function validateConnectionV2(
  arrow: { source: string; target: string },
  nodes: Map<string, Node>
): { valid: boolean; error?: string } {
  // Import bridge utilities
  const { convertNodeMap } = require('./connections/diagram-bridge');
  const diagramNodes = convertNodeMap(nodes);
  return validateTypedConnection(arrow as Arrow, diagramNodes);
}

/**
 * Find valid targets using the new typed system
 */
export function findValidTargetsV2(
  sourceNodeId: string,
  sourceHandleName: string,
  nodes: Map<string, Node>
): Array<{ nodeId: string; handleName: string; handleId: HandleID }> {
  const { convertNodeMap } = require('./connections/diagram-bridge');
  const diagramNodes = convertNodeMap(nodes);
  return findTypedValidTargets(sourceNodeId, sourceHandleName, diagramNodes);
}

/**
 * Find valid sources using the new typed system
 */
export function findValidSourcesV2(
  targetNodeId: string,
  targetHandleName: string,
  nodes: Map<string, Node>
): Array<{ nodeId: string; handleName: string; handleId: HandleID }> {
  const { convertNodeMap } = require('./connections/diagram-bridge');
  const diagramNodes = convertNodeMap(nodes);
  return findTypedValidSources(targetNodeId, targetHandleName, diagramNodes);
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
        customValidator: (from, _to) => {
          // Only allow boolean outputs from condition nodes
          return from.name === 'true' || from.name === 'false';
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