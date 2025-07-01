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
  Vec2
} from './diagram';
import { parseHandleId } from './conversions';

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
// Vec2 Conversions
// ============================================================================

/**
 * Convert Vec2 to input format (for GraphQL mutations)
 */
export function vec2ToInput(vec: Vec2): Vec2 {
  return { x: vec.x, y: vec.y };
}

/**
 * Convert from GraphQL Vec2 format
 */
export function vec2FromGraphQL(vec: { x: number; y: number }): Vec2 {
  return { x: vec.x, y: vec.y };
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
  nodeId: NodeID
): DomainHandle[] {
  return diagram.handles.filter(
    (handle) => handle.node_id === nodeId
  );
}

/**
 * Get a handle by its ID
 */
export function getHandleById(
  diagram: DomainDiagram,
  handleId: HandleID
): DomainHandle | undefined {
  return diagram.handles.find((handle) => handle.id === handleId);
}

// Re-export utilities for convenience
export { parseHandleId } from './conversions';
export { createEmptyDiagram, isDomainNode } from './diagram-utils';