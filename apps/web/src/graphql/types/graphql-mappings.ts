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
  diagramToStoreMaps as originalDiagramToStoreMaps,
  storeMapsToArrays as originalStoreMapsToArrays,
  isDomainNode,
  isDomainDiagram,
  createEmptyDiagram,
  getNodeHandles as originalGetNodeHandles,
  getHandleById as originalGetHandleById,
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

// Re-export type only
export type { StoreDiagram } from '@dipeo/domain-models';

// Wrapper function to handle GraphQL type to domain type conversion
export function diagramToStoreMaps(diagram: Partial<DomainDiagramType>): {
  nodes: Map<NodeID, DomainNodeType>;
  handles: Map<HandleID, DomainHandleType>;
  arrows: Map<ArrowID, DomainArrowType>;
  persons: Map<PersonID, DomainPersonType>;
} {
  // The types are structurally compatible, we just need to cast them
  // to satisfy TypeScript's type checking with the different ContentType enums
  return originalDiagramToStoreMaps(diagram as any) as any;
}

// Wrapper function to handle domain type to GraphQL type conversion
export function storeMapsToArrays(store: {
  nodes: Map<NodeID, DomainNode>;
  handles: Map<HandleID, DomainHandle>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
}): Partial<DomainDiagramType> {
  // The types are structurally compatible, we just need to cast them
  return originalStoreMapsToArrays(store as any) as Partial<DomainDiagramType>;
}

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


// Re-export type guards with aliases
export { isDomainNode } from '@dipeo/domain-models';
export const isReactDiagram = isDomainDiagram;

// Re-export utility functions
export { createEmptyDiagram } from '@dipeo/domain-models';

// Wrapper for getNodeHandles to handle GraphQL types
export function getNodeHandles(
  diagram: DomainDiagramType,
  nodeId: NodeID
): DomainHandleType[] {
  // Cast to domain types for the function call, then cast result back
  const domainHandles = originalGetNodeHandles(diagram as any, nodeId);
  return domainHandles as DomainHandleType[];
}

// Wrapper for getHandleById to handle GraphQL types
export function getHandleById(
  diagram: DomainDiagramType,
  handleId: HandleID
): DomainHandleType | undefined {
  const domainHandle = originalGetHandleById(diagram as any, handleId);
  return domainHandle as DomainHandleType | undefined;
}

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