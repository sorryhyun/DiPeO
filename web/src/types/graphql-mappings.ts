/**
 * Type mappings and utilities for GraphQL/Domain and React types
 * 
 * This file provides a clear separation between:
 * - Domain/GraphQL types: Used for server communication (array-based)
 * - React types: Used in React components and hooks (array-based, same structure as Domain)
 * - Store types: Used for React state management (Map-based for efficient lookups)
 */

import type {
  Node,
  Arrow,
  Handle,
  Person,
  ApiKey,
  Diagram,
  Vec2Input
} from '@/__generated__/graphql';
import { NodeType, HandleDirection, DataType } from '@/__generated__/graphql';
import type { NodeID, ArrowID, HandleID, PersonID, ApiKeyID, DiagramID } from './branded';
import type { Vec2 } from './utilities';

// Domain types are GraphQL types - they are the same
// React types are also the same structure but typed for React usage
export type DomainNode = Node;
export type DomainArrow = Arrow;
export type DomainHandle = Handle;
export type DomainPerson = Person;
export type DomainApiKey = ApiKey;
export type ReactDiagram = Diagram;

// Store format uses Maps for efficient lookups
export interface StoreDiagram {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  apiKeys: Map<ApiKeyID, ApiKey>;
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
export function diagramToStoreMaps(diagram: Partial<Diagram>): {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  apiKeys: Map<ApiKeyID, ApiKey>;
} {
  const nodes = new Map<NodeID, Node>();
  const handles = new Map<HandleID, Handle>();
  const arrows = new Map<ArrowID, Arrow>();
  const persons = new Map<PersonID, Person>();
  const apiKeys = new Map<ApiKeyID, ApiKey>();

  // Convert arrays to maps with branded IDs as keys
  diagram.nodes?.forEach(node => {
    nodes.set(node.id as NodeID, node);
  });

  diagram.handles?.forEach(handle => {
    handles.set(handle.id as HandleID, handle);
  });

  diagram.arrows?.forEach(arrow => {
    arrows.set(arrow.id as ArrowID, arrow);
  });

  diagram.persons?.forEach(person => {
    persons.set(person.id as PersonID, person);
  });

  diagram.apiKeys?.forEach(apiKey => {
    apiKeys.set(apiKey.id as ApiKeyID, apiKey);
  });

  return { nodes, handles, arrows, persons, apiKeys };
}

// Convert from Store format (Maps) back to Domain/React format (arrays)
export function storeMapsToArrays(store: {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  apiKeys: Map<ApiKeyID, ApiKey>;
}): Partial<Diagram> {
  return {
    nodes: Array.from(store.nodes.values()),
    handles: Array.from(store.handles.values()),
    arrows: Array.from(store.arrows.values()),
    persons: Array.from(store.persons.values()),
    apiKeys: Array.from(store.apiKeys.values())
  };
}

// Convert from React format to Domain/GraphQL format for server communication
export function reactDiagramToDomain(diagram: ReactDiagram): Partial<Diagram> {
  return {
    nodes: diagram.nodes || [],
    handles: diagram.handles || [],
    arrows: diagram.arrows || [],
    persons: diagram.persons || [],
    apiKeys: diagram.apiKeys || [],
    metadata: diagram.metadata ? {
      __typename: 'DiagramMetadata',
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
export function domainToReactDiagram(diagram: Partial<Diagram>): ReactDiagram {
  return diagram as ReactDiagram;
}

// Node type mappings
export function nodeKindToGraphQLType(kind: string): NodeType {
  const mapping: Record<string, NodeType> = {
    'start': NodeType.Start,
    'condition': NodeType.Condition,
    'person_job': NodeType.PersonJob,
    'person_batch_job': NodeType.PersonBatchJob,
    'endpoint': NodeType.Endpoint,
    'db': NodeType.Db,
    'job': NodeType.Job,
    'user_response': NodeType.UserResponse,
    'notion': NodeType.Notion
  };
  return mapping[kind] || NodeType.Start;
}

export function graphQLTypeToNodeKind(type: NodeType): string {
  const mapping: Record<NodeType, string> = {
    [NodeType.Start]: 'start',
    [NodeType.Condition]: 'condition',
    [NodeType.PersonJob]: 'person_job',
    [NodeType.PersonBatchJob]: 'person_batch_job',
    [NodeType.Endpoint]: 'endpoint',
    [NodeType.Db]: 'db',
    [NodeType.Job]: 'job',
    [NodeType.UserResponse]: 'user_response',
    [NodeType.Notion]: 'notion'
  };
  return mapping[type];
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
    'persons' in obj &&
    'apiKeys' in obj
  );
}

// Utility functions matching old domain helpers
export function createEmptyDiagram(): ReactDiagram {
  return {
    nodes: [],
    handles: [],
    arrows: [],
    persons: [],
    apiKeys: [],
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
): Handle[] {
  return (diagram.handles || []).filter(
    handle => handle.nodeId === nodeId
  );
}

export function getHandleById(diagram: ReactDiagram, handleId: HandleID): Handle | undefined {
  return (diagram.handles || []).find(handle => handle.id === handleId);
}

export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  const [nodeId, ...handleNameParts] = handleId.split(':');
  return {
    nodeId: nodeId as NodeID,
    handleName: handleNameParts.join(':')
  };
}

// Check if two handles are compatible for connection
export function areHandlesCompatible(source: Handle, target: Handle): boolean {
  // Basic compatibility: output can connect to input
  if (source.direction !== HandleDirection.Output || target.direction !== HandleDirection.Input) {
    return false;
  }
  
  // Type compatibility
  if (source.dataType === DataType.Any || target.dataType === DataType.Any) {
    return true;
  }
  
  return source.dataType === target.dataType;
}

// Arrow type for backward compatibility
export interface ArrowData {
  label?: string;
  [key: string]: unknown;
}