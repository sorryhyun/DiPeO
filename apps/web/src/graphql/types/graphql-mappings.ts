import type React from 'react';
import type {
  DomainNodeType,
  DomainArrowType,
  DomainHandleType,
  DomainPersonType,
  DomainApiKeyType,
  DomainDiagramType,
  Vec2Input
} from '@/__generated__/graphql';
import {
  NodeType, Vec2,
  NodeID, ArrowID, HandleID, PersonID, DiagramID,
  nodeKindToDomainType, domainTypeToNodeKind,
  areHandlesCompatible as domainAreHandlesCompatible,
  parseHandleId as domainParseHandleId
} from '@dipeo/domain-models';

// Type aliases for semantic clarity - these help distinguish between
// different contexts where the same types are used

// Domain types represent the server's data model
export type DomainNode = DomainNodeType;
export type DomainArrow = DomainArrowType;
export type DomainHandle = DomainHandleType;
export type DomainPerson = DomainPersonType;
export type DomainApiKey = DomainApiKeyType;
export type DomainDiagram = DomainDiagramType;

export type ReactDiagram = DomainDiagramType;

// Store format uses Maps for efficient lookups
export interface StoreDiagram {
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  metadata?: {
    id?: DiagramID;
    name?: string;
    description?: string;
    version: string;
    created: string;
    modified: string;
    author?: string;
    tags?: string[];
  };
}

// Convert from Domain/React format (arrays) to Store format (Maps)
export function diagramToStoreMaps(diagram: Partial<DomainDiagramType>): {
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
} {
  // Manually convert because of type differences between GraphQL and domain types
  const nodes = new Map<NodeID, DomainNode>();
  const handles = new Map<HandleID, DomainHandle>();
  const arrows = new Map<ArrowID, DomainArrow>();
  const persons = new Map<PersonID, DomainPerson>();

  // Convert arrays to maps with branded IDs as keys
  diagram.nodes?.forEach((node: DomainNode) => {
    nodes.set(node.id as NodeID, node);
  });

  diagram.handles?.forEach((handle: DomainHandle) => {
    handles.set(handle.id as HandleID, handle);
  });

  diagram.arrows?.forEach((arrow: DomainArrow) => {
    arrows.set(arrow.id as ArrowID, arrow);
  });

  diagram.persons?.forEach((person: DomainPerson) => {
    persons.set(person.id as PersonID, person);
  });

  return { nodes, handles, arrows, persons };
}

// Convert from Store format (Maps) back to Domain/React format (arrays)
export function storeMapsToArrays(store: {
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
}): Partial<DomainDiagramType> {
  return {
    nodes: Array.from(store.nodes.values()),
    handles: Array.from(store.handles.values()),
    arrows: Array.from(store.arrows.values()),
    persons: Array.from(store.persons.values())
  };
}

// Convert from React format to Domain/GraphQL format for server communication
export function reactDiagramToDomain(diagram: ReactDiagram): Partial<DomainDiagramType> {
  return {
    nodes: diagram.nodes || [],
    handles: diagram.handles || [],
    arrows: diagram.arrows || [],
    persons: diagram.persons || [],
    metadata: diagram.metadata ? {
      __typename: 'DiagramMetadataType' as const,
      id: diagram.metadata.id || null,
      name: diagram.metadata.name || null,
      description: diagram.metadata.description || null,
      version: diagram.metadata.version,
      created: diagram.metadata.created,
      modified: diagram.metadata.modified,
      author: diagram.metadata.author || null,
      tags: diagram.metadata.tags || null
    } : undefined
  };
}

// Convert from Domain/GraphQL format to React format for component usage
export function domainToReactDiagram(diagram: Partial<DomainDiagramType>): ReactDiagram {
  return diagram as ReactDiagram;
}

// Node type mappings - delegate to centralized conversions
export function nodeKindToGraphQLType(kind: string): NodeType {
  // Convert snake_case to camelCase if needed
  const camelCaseKind = kind.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
  return nodeKindToDomainType(camelCaseKind);
}

export function graphQLTypeToNodeKind(type: NodeType): string {
  const camelCaseKind = domainTypeToNodeKind(type);
  // Convert camelCase back to snake_case if needed
  return camelCaseKind.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

// Vec2 conversion helpers
export function vec2ToInput(vec: Vec2): Vec2Input {
  return { x: vec.x, y: vec.y };
}

export function vec2FromGraphQL(vec: { x: number; y: number }): Vec2 {
  return { x: vec.x, y: vec.y };
}

// Type guards (matching old domain type guards)
export function isDomainNode(obj: unknown): obj is Node {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'type' in obj &&
    'position' in obj &&
    'data' in obj
  );
}

export function isReactDiagram(obj: unknown): obj is ReactDiagram {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'nodes' in obj &&
    'handles' in obj &&
    'arrows' in obj &&
    'persons' in obj
  );
}

// Utility functions matching old domain helpers
export function createEmptyDiagram(): ReactDiagram {
  return {
    nodes: [],
    handles: [],
    arrows: [],
    persons: [],
    nodeCount: 0,
    arrowCount: 0,
    personCount: 0,
    metadata: {
      version: '2.0.0',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    }
  };
}

export function getNodeHandles(
  diagram: ReactDiagram,
  nodeId: NodeID
): DomainHandle[] {
  return (diagram.handles || []).filter(
    (handle: DomainHandle) => handle.nodeId === nodeId
  );
}

export function getHandleById(diagram: ReactDiagram, handleId: HandleID): DomainHandle | undefined {
  return (diagram.handles || []).find((handle: DomainHandle) => handle.id === handleId);
}

export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  // Use centralized implementation, but adapt return type names
  const result = domainParseHandleId(handleId);
  return {
    nodeId: result.nodeId,
    handleName: result.handleLabel // Note: centralized version uses 'handleLabel'
  };
}

// Check if two handles are compatible for connection
export function areHandlesCompatible(source: DomainHandle, target: DomainHandle): boolean {
  // Convert GraphQL handles to domain format for compatibility check
  const sourceHandle = {
    ...source,
    id: source.id as HandleID,
    nodeId: source.nodeId as NodeID
  };
  const targetHandle = {
    ...target,
    id: target.id as HandleID,
    nodeId: target.nodeId as NodeID
  };
  
  // Use centralized compatibility check
  return domainAreHandlesCompatible(sourceHandle, targetHandle);
}

// Arrow data interface
export interface ArrowData {
  label?: string;
  style?: React.CSSProperties;
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  loopRadius?: number;
  branch?: 'true' | 'false';
  contentType?: 'raw_text' | 'variable_in_object' | 'conversation_state' | 'empty' | 'generic';
  [key: string]: unknown;
}