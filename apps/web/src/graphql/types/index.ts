
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
  reactDiagramToDomain,
  domainToReactDiagram,
  nodeKindToGraphQLType,
  graphQLTypeToNodeKind,
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