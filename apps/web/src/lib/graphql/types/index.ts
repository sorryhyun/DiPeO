
// Re-export generated GraphQL types directly
export type {
  DomainNodeType as Node,
  DomainArrowType as Arrow,
  DomainHandleType as Handle,
  DomainPersonType as Person,
  DomainApiKeyType as ApiKey,
  DomainDiagramType,
  Vec2Input,
  // Any other types needed from GraphQL
} from '@/__generated__/graphql';

// Re-export utilities and conversions from mappings
export {
  diagramToStoreMaps,
  storeMapsToArrays,
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain,
  nodeKindToGraphQLType,
  graphQLTypeToNodeKind,
  isDomainNode,
  isDomainDiagram,
  areHandlesCompatible,
  getNodeHandles,
  getHandleById,
  parseHandleId,
  createEmptyDiagram,
  type StoreDiagram,
  type ArrowData
} from './graphql-mappings';

// Re-export GraphQL types directly (semantic aliases)
export type {
  DomainNodeType as DomainNode,
  DomainArrowType as DomainArrow,
  DomainHandleType as DomainHandle,
  DomainPersonType as DomainPerson,
  DomainApiKeyType as DomainApiKey,
  DomainDiagramType as DomainDiagram
} from './graphql-mappings';