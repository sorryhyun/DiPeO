/**
 * GraphQL and store format conversions for DiPeO domain models.
 * These utilities handle conversions between different data representations.
 */

import {
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  DiagramID,
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainDiagram,
  DiagramMetadata,
  Vec2,
  PersonLLMConfig
} from './diagram';
import { parseHandleId } from './conversions';

// GraphQL types (imported for conversion)
export interface GraphQLDomainPersonType {
  id: string;
  label: string;
  llm_config: PersonLLMConfig;
  type: string;
  masked_api_key?: string | null;
}

// ============================================================================
// Store Format Types
// ============================================================================

/**
 * Store format uses Maps for efficient lookups in frontend state management
 */
export interface StoreDiagram {
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  metadata?: DiagramMetadata;
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
    masked_api_key: graphqlPerson.masked_api_key || null,
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

// ============================================================================
// Array <-> Map Conversions
// ============================================================================

/**
 * Convert from Domain format (arrays) to Store format (Maps)
 * Used when loading diagrams into frontend state
 */
export function diagramToStoreMaps(diagram: Partial<DomainDiagram>): {
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
} {
  const nodes = new Map<NodeID, DomainNode>();
  const handles = new Map<HandleID, DomainHandle>();
  const arrows = new Map<ArrowID, DomainArrow>();
  const persons = new Map<PersonID, DomainPerson>();

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
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
}): Partial<DomainDiagram> {
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
 * Check if an object is a valid DomainDiagram
 */
export function isDomainDiagram(obj: unknown): obj is DomainDiagram {
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
  diagram: DomainDiagram,
  node_id: NodeID
): DomainHandle[] {
  return diagram.handles.filter(
    (handle) => handle.node_id === node_id
  );
}

/**
 * Get a handle by its ID
 */
export function getHandleById(
  diagram: DomainDiagram,
  handle_id: HandleID
): DomainHandle | undefined {
  return diagram.handles.find((handle) => handle.id === handle_id);
}

// Re-export utilities for convenience
export { parseHandleId } from './conversions';
export { createEmptyDiagram, isDomainNode } from './diagram-utils';