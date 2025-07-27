
// Re-export generated GraphQL types with semantic aliases
export type {
  DomainNodeType as DomainNode,
  DomainArrowType as DomainArrow,
  DomainHandleType as DomainHandle,
  DomainPersonType as DomainPerson,
  DomainApiKeyType as DomainApiKey,
  DomainDiagramType as DomainDiagram,
  DomainDiagramType,
  Vec2Input
} from '@/__generated__/graphql';

// Re-export utilities and conversions from mappings
export {
  diagramArraysToMaps,
  diagramMapsToArrays,
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain,
  nodeKindToGraphQLType,
  graphQLTypeToNodeKind,
  isDomainNode,
  areHandlesCompatible,
  parseHandleId,
  createEmptyDiagram,
  type ArrowData
} from './graphql-mappings';