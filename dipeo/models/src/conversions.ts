/**
 * Conversion utilities for DiPeO domain models.
 * Includes domain conversions and GraphQL/store format conversions.
 */

import {
  NodeType,
  HandleDirection,
  HandleLabel,
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainDiagram,
  PersonLLMConfig,
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
  // Handle both uppercase and lowercase node kinds
  const normalizedKind = kind.toLowerCase();
  const domainType = NODE_TYPE_MAP[normalizedKind];
  if (!domainType) {
    throw new Error(`Unknown node kind: ${kind}`);
  }
  return domainType;
}

/**
 * Convert domain node type to frontend node type
 */
export function domainTypeToNodeKind(type: NodeType | string): string {
  // Handle uppercase string values from GraphQL by converting to lowercase
  const normalizedType = typeof type === 'string' ? type.toLowerCase() : type;
  const kind = NODE_TYPE_REVERSE_MAP[normalizedType as NodeType];
  
  if (!kind) {
    throw new Error(`Unknown node type: ${type}`);
  }
  return kind;
}

// ============================================================================
// Handle ID Management
// ============================================================================

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
  
  // Same type is always compatible
  if (sourceHandle.data_type === targetHandle.data_type) {
    return true;
  }
  
  // 'any' type is compatible with everything
  return sourceHandle.data_type === 'any' || targetHandle.data_type === 'any';
}

// ============================================================================
// Data Structure Conversions
// ============================================================================

/**
 * Convert array-based diagram to map-based structure
 */
export function diagramArraysToMaps(diagram: Partial<{
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
}>): {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
} {
  return {
    nodes: new Map(diagram.nodes?.map(n => [n.id, n]) ?? []),
    arrows: new Map(diagram.arrows?.map(a => [a.id, a]) ?? []),
    handles: new Map(diagram.handles?.map(h => [h.id, h]) ?? []),
    persons: new Map(diagram.persons?.map(p => [p.id, p]) ?? []),
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
}): {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
} {
  return {
    nodes: Array.from(diagram.nodes.values()),
    arrows: Array.from(diagram.arrows.values()),
    handles: Array.from(diagram.handles.values()),
    persons: Array.from(diagram.persons.values()),
  };
}

// ============================================================================
// GraphQL Type Conversions
// ============================================================================

/**
 * Convert GraphQL DomainPersonType to domain DomainPerson
 * Handles the api_key_id optional/required mismatch
 */
export function convertGraphQLPersonToDomain(graphqlPerson: any): DomainPerson {
  // Handle missing or null api_key_id by providing a default value
  const apiKeyId = graphqlPerson.llm_config?.api_key_id || '';
  
  return {
    id: graphqlPerson.id as PersonID,
    label: graphqlPerson.label,
    llm_config: {
      service: graphqlPerson.llm_config.service,
      model: graphqlPerson.llm_config.model,
      api_key_id: apiKeyId,
      system_prompt: graphqlPerson.llm_config.system_prompt || null,
    } as PersonLLMConfig,
    type: 'person' as const,
  };
}

/**
 * Convert GraphQL diagram data to domain format, handling type mismatches
 */
export function convertGraphQLDiagramToDomain(diagram: any): Partial<DomainDiagram> {
  const result: Partial<DomainDiagram> = {};
  
  if (diagram.nodes) {
    result.nodes = diagram.nodes;
  }
  
  if (diagram.handles) {
    result.handles = diagram.handles;
  }
  
  if (diagram.arrows) {
    result.arrows = diagram.arrows;
  }
  
  if (diagram.persons) {
    result.persons = diagram.persons.map(convertGraphQLPersonToDomain);
  }
  
  return result;
}

