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
  // convertGraphQLDiagramToDomain, // Moved to generated mappings
  // convertGraphQLPersonToDomain, // Moved to generated mappings
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

// Import and re-export conversion functions from generated mappings
import { 
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain 
} from '@/__generated__/domain/mappings';

export {
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain
};

// Arrow data interface
export interface ArrowData {
  label?: string;
  style?: React.CSSProperties;
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  loopRadius?: number;
  branch?: 'true' | 'false';
  content_type?: 'raw_text' | 'variable_in_object' | 'conversation_state' | 'empty' | 'generic';
  [key: string]: unknown;
}