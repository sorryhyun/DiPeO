/**
 * GraphQL Type Exports
 * 
 * This file provides a clean interface for accessing GraphQL-generated types
 * and related utilities throughout the application.
 * 
 * CONSOLIDATION NOTE:
 * This reduces the re-declaration of GraphQL types by:
 * 1. Directly exporting generated types from @/__generated__/graphql
 * 2. Keeping semantic aliases (Domain*, React*) only in graphql-mappings for backward compatibility
 * 3. Providing a single import point for all GraphQL-related types and utilities
 * 
 * Import from here when you need GraphQL types or conversion utilities.
 */

// Re-export generated GraphQL types directly
export type {
  DomainNode as Node,
  DomainArrow as Arrow,
  DomainHandle as Handle,
  DomainPerson as Person,
  DomainApiKey as ApiKey,
  DomainDiagramType,
  Vec2Input,
  // Any other types needed from GraphQL
} from '@/__generated__/graphql';

// Re-export utilities and conversions from mappings
export {
  diagramToStoreMaps,
  storeMapsToArrays,
  reactDiagramToDomain,
  domainToReactDiagram,
  nodeKindToGraphQLType,
  graphQLTypeToNodeKind,
  vec2ToInput,
  vec2FromGraphQL,
  isDomainNode,
  isReactDiagram,
  areHandlesCompatible,
  getNodeHandles,
  getHandleById,
  parseHandleId,
  createEmptyDiagram,
  type StoreDiagram,
  type ArrowData
} from './graphql-mappings';

// Re-export semantic type aliases from mappings
export type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  DomainDiagram,
  ReactDiagram
} from './graphql-mappings';