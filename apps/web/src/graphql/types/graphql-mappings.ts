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
  parseHandleId as domainParseHandleId,
  diagramToStoreMaps,
  storeMapsToArrays,
  vec2ToInput,
  vec2FromGraphQL,
  isDomainNode,
  isDomainDiagram,
  createEmptyDiagram,
  getNodeHandles,
  getHandleById,
  StoreDiagram
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

// Re-export centralized conversions
export { diagramToStoreMaps, storeMapsToArrays, StoreDiagram } from '@dipeo/domain-models';

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

// Node type mappings - use centralized conversions directly
export const nodeKindToGraphQLType = nodeKindToDomainType;
export const graphQLTypeToNodeKind = domainTypeToNodeKind;

// Re-export Vec2 conversions
export { vec2ToInput, vec2FromGraphQL } from '@dipeo/domain-models';

// Re-export type guards with aliases
export { isDomainNode } from '@dipeo/domain-models';
export const isReactDiagram = isDomainDiagram;

// Re-export utility functions
export { createEmptyDiagram, getNodeHandles, getHandleById } from '@dipeo/domain-models';

export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  // Use centralized implementation, but adapt return type names
  const result = domainParseHandleId(handleId);
  return {
    nodeId: result.node_id,
    handleName: result.handle_label
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