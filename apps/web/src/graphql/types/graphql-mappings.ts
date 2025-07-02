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
export { diagramToStoreMaps, storeMapsToArrays } from '@dipeo/domain-models';
export type { StoreDiagram } from '@dipeo/domain-models';

// Convert from React format to Domain/GraphQL format for server communication
export function reactDiagramToDomain(diagram: ReactDiagram): Partial<DomainDiagramType> {
  return diagram;
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
export const areHandlesCompatible = domainAreHandlesCompatible;

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