/**
 * GraphQL and store format conversions for DiPeO domain models.
 * These utilities handle conversions between different data representations.
 */

import {
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  Node,
  Arrow,
  Handle,
  Person,
  Diagram,
  DiagramMetadata,
  PersonLLMConfig
} from './diagram';

// GraphQL types (imported for conversion)
export interface GraphQLDomainPersonType {
  id: string;
  label: string;
  llm_config: PersonLLMConfig;
  type: string;
}

// ============================================================================
// Store Format Types
// ============================================================================

/**
 * Store format uses Maps for efficient lookups in frontend state management
 */
export interface StoreDiagram {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  metadata?: DiagramMetadata;
}

// ============================================================================
// GraphQL Type Conversions
// ============================================================================

/**
 * Convert GraphQL DomainPersonType to domain Person
 * Handles the api_key_id optional/required mismatch
 */
export function convertGraphQLPersonToDomain(graphqlPerson: any): Person {
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
export function convertGraphQLDiagramToDomain(diagram: any): Partial<Diagram> {
  const result: Partial<Diagram> = {};
  
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

// ============================================================================
// Array <-> Map Conversions
// ============================================================================

/**
 * Convert from Domain format (arrays) to Store format (Maps)
 * Used when loading diagrams into frontend state
 */
export function diagramToStoreMaps(diagram: Partial<Diagram>): {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
} {
  const nodes = new Map<NodeID, Node>();
  const handles = new Map<HandleID, Handle>();
  const arrows = new Map<ArrowID, Arrow>();
  const persons = new Map<PersonID, Person>();

  // Convert arrays to maps with branded IDs as keys
  diagram.nodes?.forEach((node) => {
    nodes.set(node.id, node);
  });

  diagram.handles?.forEach((handle) => {
    handles.set(handle.id, handle);
  });

  diagram.arrows?.forEach((arrow) => {
    arrows.set(arrow.id, arrow);
  });

  diagram.persons?.forEach((person) => {
    persons.set(person.id, person);
  });

  return { nodes, handles, arrows, persons };
}

/**
 * Convert from Store format (Maps) back to Domain format (arrays)
 * Used when sending diagrams to server or saving
 */
export function storeMapsToArrays(store: {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
}): Partial<Diagram> {
  return {
    nodes: Array.from(store.nodes.values()),
    handles: Array.from(store.handles.values()),
    arrows: Array.from(store.arrows.values()),
    persons: Array.from(store.persons.values())
  };
}


// ============================================================================
// Type Guards
// ============================================================================

/**
 * Check if an object is a valid Diagram
 */
export function isDiagram(obj: unknown): obj is Diagram {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'nodes' in obj &&
    'handles' in obj &&
    'arrows' in obj &&
    'persons' in obj
  );
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get all handles for a specific node
 */
export function getNodeHandles(
  diagram: Diagram,
  node_id: NodeID
): Handle[] {
  return diagram.handles.filter(
    (handle) => handle.node_id === node_id
  );
}

/**
 * Get a handle by its ID
 */
export function getHandleById(
  diagram: Diagram,
  handle_id: HandleID
): Handle | undefined {
  return diagram.handles.find((handle) => handle.id === handle_id);
}

// Re-export utilities for convenience
export { parseHandleId } from './conversions';
export { createEmptyDiagram, isNode } from './diagram-utils';