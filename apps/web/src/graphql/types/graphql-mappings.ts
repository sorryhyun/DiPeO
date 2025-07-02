import type React from 'react';
import {
  NodeID, ArrowID, HandleID, PersonID, DiagramID,
  parseHandleId as domainParseHandleId
} from '@dipeo/domain-models';

// Re-export GraphQL types directly
export type {
  DomainNodeType,
  DomainArrowType,
  DomainHandleType,
  DomainPersonType,
  DomainApiKeyType,
  DomainDiagramType,
  Vec2Input
} from '@/__generated__/graphql';


// Re-export type only
export type { StoreDiagram } from '@dipeo/domain-models';

// Re-export conversion functions directly from domain models
export {
  diagramToStoreMaps,
  storeMapsToArrays,
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain
} from '@dipeo/domain-models';


// Re-export node type conversions directly
export {
  nodeKindToDomainType as nodeKindToGraphQLType,
  domainTypeToNodeKind as graphQLTypeToNodeKind
} from '@dipeo/domain-models';


// Re-export type guards
export { isDomainNode, isDomainDiagram } from '@dipeo/domain-models';

// Re-export utility functions
export { createEmptyDiagram } from '@dipeo/domain-models';

// Re-export handle utility functions directly
export {
  getNodeHandles,
  getHandleById
} from '@dipeo/domain-models';

export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  // Use centralized implementation, but adapt return type names
  const result = domainParseHandleId(handleId);
  return {
    nodeId: result.node_id,
    handleName: result.handle_label
  };
}

// Re-export handle compatibility check
export { areHandlesCompatible } from '@dipeo/domain-models';

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