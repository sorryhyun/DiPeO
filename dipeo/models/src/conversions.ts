/**
 * Single-source conversion utilities for DiPeO domain models.
 * These utilities are code-generated to Python to ensure consistency.
 */

import {
  NodeType,
  HandleDirection,
  HandleLabel,
  DataType,
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  ApiKeyID,
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
} from './diagram';

// ============================================================================
// Node Type Mapping
// ============================================================================

/**
 * Maps node type strings to GraphQL/domain node types
 */
export const NODE_TYPE_MAP: Record<string, NodeType> = {
  'code_job': NodeType.CODE_JOB,
  'api_job': NodeType.API_JOB,
  'person_job': NodeType.PERSON_JOB,
  'person_batch_job': NodeType.PERSON_BATCH_JOB,
  'condition': NodeType.CONDITION,
  'user_response': NodeType.USER_RESPONSE,
  'start': NodeType.START,
  'endpoint': NodeType.ENDPOINT,
  'db': NodeType.DB,
  'notion': NodeType.NOTION,
  'hook': NodeType.HOOK,
  'template_job': NodeType.TEMPLATE_JOB,
  'json_schema_validator': NodeType.JSON_SCHEMA_VALIDATOR,
  'typescript_ast': NodeType.TYPESCRIPT_AST,
  'sub_diagram': NodeType.SUB_DIAGRAM,
} as const;

/**
 * Reverse mapping from domain node types to frontend types
 */
export const NODE_TYPE_REVERSE_MAP: Record<NodeType, string> = Object.entries(NODE_TYPE_MAP)
  .reduce((acc, [key, value]) => ({ ...acc, [value]: key }), {} as Record<NodeType, string>);

/**
 * Convert frontend node type to domain node type
 */
export function nodeKindToDomainType(kind: string): NodeType {
  const domainType = NODE_TYPE_MAP[kind];
  if (!domainType) {
    throw new Error(`Unknown node kind: ${kind}`);
  }
  return domainType;
}

/**
 * Convert domain node type to frontend node type
 */
export function domainTypeToNodeKind(type: NodeType): string {
  const kind = NODE_TYPE_REVERSE_MAP[type];
  if (!kind) {
    throw new Error(`Unknown node type: ${type}`);
  }
  return kind;
}

// ============================================================================
// Handle ID Management
// ============================================================================

/**
 * Normalize a node ID to ensure consistent casing
 */
export function normalizeNodeId(nodeId: string): NodeID {
  // For now, we keep the original casing for node IDs
  // This allows both uppercase and lowercase to work
  return nodeId as NodeID;
}

/**
 * Create a handle ID from node ID, handle label, and direction
 * Format: [nodeId]_[handleLabel]_[direction]
 */
export function createHandleId(
  nodeId: NodeID,
  handleLabel: HandleLabel,
  direction: HandleDirection
): HandleID {
  // Use underscores for simpler format
  return `${nodeId}_${handleLabel}_${direction}` as HandleID;
}

/**
 * Parse a handle ID into its components
 * Returns (node_id, handle_label, direction)
 */
export function parseHandleId(
  handleId: HandleID
): { node_id: NodeID; handle_label: HandleLabel; direction: HandleDirection } {
  // Format: [nodeId]_[handleLabel]_[direction]
  const parts = handleId.split('_');
  if (parts.length < 3) {
    throw new Error(`Invalid handle ID format: ${handleId}`);
  }
  
  // Extract parts: nodeId_label_direction
  const direction = parts[parts.length - 1] as HandleDirection;
  const handleLabel = parts[parts.length - 2] as HandleLabel;
  const nodeIdParts = parts.slice(0, -2);
  const nodeId = nodeIdParts.join('_');
  
  if (!nodeId || !handleLabel || !Object.values(HandleDirection).includes(direction)) {
    throw new Error(`Invalid handle ID format: ${handleId}`);
  }
  
  // Validate handle label
  if (!Object.values(HandleLabel).includes(handleLabel)) {
    throw new Error(`Invalid handle label in handle ID: ${handleId}`);
  }
  
  return {
    node_id: nodeId as NodeID,
    handle_label: handleLabel,
    direction,
  };
}

// ============================================================================
// Handle Compatibility
// ============================================================================

/**
 * Check if two handles are compatible for connection
 */
export function areHandlesCompatible(
  sourceHandle: DomainHandle,
  targetHandle: DomainHandle
): boolean {
  // Opposite directions required
  if (sourceHandle.direction === targetHandle.direction) {
    return false;
  }
  
  // Output must connect to input
  if (sourceHandle.direction !== HandleDirection.OUTPUT) {
    return false;
  }
  
  // Check data type compatibility
  return isDataTypeCompatible(sourceHandle.data_type, targetHandle.data_type);
}

/**
 * Check if source data type is compatible with target data type
 */
export function isDataTypeCompatible(
  sourceType: DataType,
  targetType: DataType
): boolean {
  // Same type is always compatible
  if (sourceType === targetType) {
    return true;
  }
  
  // 'any' type is compatible with everything
  if (sourceType === DataType.ANY || targetType === DataType.ANY) {
    return true;
  }
  
  // Type-specific compatibility rules
  const compatibilityRules: Record<DataType, DataType[]> = {
    [DataType.STRING]: [DataType.ANY],
    [DataType.NUMBER]: [DataType.ANY],
    [DataType.BOOLEAN]: [DataType.ANY],
    [DataType.OBJECT]: [DataType.ANY],
    [DataType.ARRAY]: [DataType.ANY],
    [DataType.ANY]: Object.values(DataType),
  };
  
  return compatibilityRules[sourceType]?.includes(targetType) ?? false;
}

// ============================================================================
// Data Structure Conversions
// ============================================================================

/**
 * Convert array-based diagram to map-based structure
 */
export function diagramArraysToMaps(diagram: {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
  apiKeys?: DomainApiKey[];
}): {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
  apiKeys: Map<ApiKeyID, DomainApiKey>;
} {
  return {
    nodes: new Map(diagram.nodes.map(n => [n.id, n])),
    arrows: new Map(diagram.arrows.map(a => [a.id, a])),
    handles: new Map(diagram.handles.map(h => [h.id, h])),
    persons: new Map(diagram.persons.map(p => [p.id, p])),
    apiKeys: new Map((diagram.apiKeys || []).map(k => [k.id, k])),
  };
}

/**
 * Convert map-based diagram to array-based structure
 */
export function diagramMapsToArrays(diagram: {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
  apiKeys?: Map<ApiKeyID, DomainApiKey>;
}): {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
  apiKeys: DomainApiKey[];
} {
  return {
    nodes: Array.from(diagram.nodes.values()),
    arrows: Array.from(diagram.arrows.values()),
    handles: Array.from(diagram.handles.values()),
    persons: Array.from(diagram.persons.values()),
    apiKeys: diagram.apiKeys ? Array.from(diagram.apiKeys.values()) : [],
  };
}

// ============================================================================
// Position Calculations
// ============================================================================

/**
 * Calculate handle position offset based on direction
 */
export function calculateHandleOffset(
  direction: HandleDirection,
  index: number,
  total: number,
  nodeWidth: number = 200,
  nodeHeight: number = 100
): { x: number; y: number } {
  const spacing = 30;
  const startOffset = (total - 1) * spacing / 2;
  
  switch (direction) {
    case HandleDirection.INPUT:
      return {
        x: nodeWidth / 2,
        y: -startOffset + (index * spacing),
      };
    
    case HandleDirection.OUTPUT:
      return {
        x: nodeWidth / 2,
        y: nodeHeight + startOffset - (index * spacing),
      };
    
    default:
      return { x: nodeWidth / 2, y: nodeHeight / 2 };
  }
}

/**
 * Calculate absolute handle position
 */
export function calculateHandlePosition(
  nodePosition: { x: number; y: number },
  handleOffset: { x: number; y: number }
): { x: number; y: number } {
  return {
    x: nodePosition.x + handleOffset.x,
    y: nodePosition.y + handleOffset.y,
  };
}

// ============================================================================
// Validation Utilities
// ============================================================================

/**
 * Validate node data based on node type
 */
export function validateNodeData(
  type: NodeType,
  data: Record<string, any>
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Type-specific validation rules
  switch (type) {
    case NodeType.PERSON_JOB:
    case NodeType.PERSON_BATCH_JOB:
      if (!data.personId) {
        errors.push('Person ID is required for person job nodes');
      }
      if (!data.userPrompt && !data.systemPrompt) {
        errors.push('Either user prompt or system prompt is required');
      }
      break;
    
    case NodeType.CONDITION:
      if (!data.personId) {
        errors.push('Person ID is required for condition nodes');
      }
      if (!data.prompt) {
        errors.push('Prompt is required for condition nodes');
      }
      break;
    
    case NodeType.DB:
      if (!data.operation) {
        errors.push('Database operation is required');
      }
      if (!['query', 'insert', 'update', 'delete'].includes(data.operation)) {
        errors.push('Invalid database operation');
      }
      break;
    
    case NodeType.ENDPOINT:
      if (!data.method) {
        errors.push('HTTP method is required');
      }
      if (!data.url) {
        errors.push('URL is required');
      }
      break;
    
    case NodeType.CODE_JOB:
      if (!data.language) {
        errors.push('Language is required for code job nodes');
      }
      if (!data.code) {
        errors.push('Code is required for code job nodes');
      }
      break;
    
    case NodeType.API_JOB:
      if (!data.url) {
        errors.push('URL is required for API job nodes');
      }
      if (!data.method) {
        errors.push('HTTP method is required for API job nodes');
      }
      break;
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate arrow connection
 */
export function validateArrowConnection(
  sourceNode: DomainNode,
  targetNode: DomainNode,
  sourceHandle: DomainHandle,
  targetHandle: DomainHandle
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Check handle ownership
  if (parseHandleId(sourceHandle.id).node_id !== sourceNode.id) {
    errors.push('Source handle does not belong to source node');
  }
  
  if (parseHandleId(targetHandle.id).node_id !== targetNode.id) {
    errors.push('Target handle does not belong to target node');
  }
  
  // Check handle compatibility
  if (!areHandlesCompatible(sourceHandle, targetHandle)) {
    errors.push('Handles are not compatible for connection');
  }
  
  // Node-specific connection rules
  if (sourceNode.type === NodeType.START && sourceNode.data?.connections?.length > 0) {
    errors.push('Start node can only have one outgoing connection');
  }
  
  if (targetNode.type === NodeType.START) {
    errors.push('Cannot connect to start node');
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}