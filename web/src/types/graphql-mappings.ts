/**
 * Type mappings and utilities for transitioning from domain types to GraphQL types
 * 
 * This file provides compatibility layer between the old domain types structure
 * (Record-based) and the new GraphQL types (Array-based).
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
import { NodeType } from '@/__generated__/graphql';
import type { NodeID, ArrowID, HandleID, PersonID, ApiKeyID } from './branded';
import type { Vec2 } from './primitives';

// Re-export GraphQL types with Domain prefix for compatibility
export type DomainNode = Node;
export type DomainArrow = Arrow;
export type DomainHandle = Handle;
export type DomainPerson = Person;
export type DomainApiKey = ApiKey;

// Create compatible diagram type that matches old structure
export interface DomainDiagram {
  nodes: Record<NodeID, Node>;
  handles: Record<HandleID, Handle>;
  arrows: Record<ArrowID, Arrow>;
  persons: Record<PersonID, Person>;
  apiKeys: Record<ApiKeyID, ApiKey>;
  metadata?: {
    id?: string;
    name?: string;
    description?: string;
    version: string;
    created: string;
    modified: string;
    author?: string;
    tags?: string[];
  };
}

// Utility functions to convert between structures
export function graphQLDiagramToDomain(diagram: Diagram): DomainDiagram {
  const nodes: Record<NodeID, Node> = {};
  const handles: Record<HandleID, Handle> = {};
  const arrows: Record<ArrowID, Arrow> = {};
  const persons: Record<PersonID, Person> = {};
  const apiKeys: Record<ApiKeyID, ApiKey> = {};

  // Convert arrays to records
  diagram.nodes.forEach(node => {
    nodes[node.id as NodeID] = node;
  });

  diagram.handles.forEach(handle => {
    handles[handle.id as HandleID] = handle;
  });

  diagram.arrows.forEach(arrow => {
    arrows[arrow.id as ArrowID] = arrow;
  });

  diagram.persons.forEach(person => {
    persons[person.id as PersonID] = person;
  });

  diagram.apiKeys.forEach(apiKey => {
    apiKeys[apiKey.id as ApiKeyID] = apiKey;
  });

  return {
    nodes,
    handles,
    arrows,
    persons,
    apiKeys,
    metadata: diagram.metadata ? {
      id: diagram.metadata.id || undefined,
      name: diagram.metadata.name || undefined,
      description: diagram.metadata.description || undefined,
      version: diagram.metadata.version,
      created: diagram.metadata.created,
      modified: diagram.metadata.modified,
      author: diagram.metadata.author || undefined,
      tags: diagram.metadata.tags || undefined
    } : undefined
  };
}

export function domainDiagramToGraphQL(diagram: DomainDiagram): Partial<Diagram> {
  return {
    nodes: Object.values(diagram.nodes),
    handles: Object.values(diagram.handles),
    arrows: Object.values(diagram.arrows),
    persons: Object.values(diagram.persons),
    apiKeys: Object.values(diagram.apiKeys),
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

export function isDomainDiagram(obj: unknown): obj is DomainDiagram {
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
export function createEmptyDiagram(): DomainDiagram {
  return {
    nodes: {},
    handles: {},
    arrows: {},
    persons: {},
    apiKeys: {},
    metadata: {
      version: '2.0.0',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    }
  };
}

export function getNodeHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): Handle[] {
  return Object.values(diagram.handles).filter(
    handle => handle.nodeId === nodeId
  );
}

export function getHandleById(diagram: DomainDiagram, handleId: HandleID): Handle | undefined {
  return diagram.handles[handleId];
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
  if (source.direction !== 'output' || target.direction !== 'input') {
    return false;
  }
  
  // Type compatibility
  if (source.dataType === 'any' || target.dataType === 'any') {
    return true;
  }
  
  return source.dataType === target.dataType;
}

// Arrow type for backward compatibility
export interface ArrowData {
  label?: string;
  [key: string]: unknown;
}