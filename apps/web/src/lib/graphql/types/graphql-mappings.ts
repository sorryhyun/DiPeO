/**
 * GraphQL-specific type mappings and utilities
 * Domain types and utilities should be imported from '@/core/types/domain'
 */

import type React from 'react';

// GraphQL-specific type exports
export type {
  DomainNodeType,
  DomainArrowType,
  DomainHandleType,
  DomainPersonType,
  DomainApiKeyType,
  DomainDiagramType,
  Vec2Input
} from '@/__generated__/graphql';

// All domain utilities are now centralized in @/core/types/domain
// Re-export them here for backward compatibility only
// TODO: Update consumers to import from '@/core/types/domain' directly
export {
  // Types
  type StoreDiagram,
  type NodeID,
  type HandleID,
  // Conversion functions
  diagramToStoreMaps,
  storeMapsToArrays,
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain,
  nodeKindToDomainType as nodeKindToGraphQLType,
  domainTypeToNodeKind as graphQLTypeToNodeKind,
  // Type guards
  isDomainNode,
  isDomainDiagram,
  // Utility functions
  createEmptyDiagram,
  getNodeHandles,
  getHandleById,
  parseHandleId,
  areHandlesCompatible
} from '@/core/types/domain';

// Arrow data interface
export interface ArrowData {
  label?: string;
  style?: React.CSSProperties;
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  loopRadius?: number;
  branch?: 'true' | 'false';
  content_type?: 'raw_text' | 'conversation_state' | 'object' | 'empty' | 'generic';
  [key: string]: unknown;
}