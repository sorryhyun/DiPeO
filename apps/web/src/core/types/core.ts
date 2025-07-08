// Re-export domain types from centralized location
export * from './domain';

// Re-export type factory utilities
export {
  type NodeTypeRegistry,
  type NodeTypeKey,
  type NodeDataTypes,
  type NodeData,
  type NodeFormData,
  type NodeFormDataTypes,
  type PanelFormData,
  isNodeTypeKey
} from './type-factories';

// Re-export GraphQL-specific types that are not in domain models
// TODO: These should eventually be moved to GraphQL layer
export type { ArrowData } from '@/lib/graphql/types';

// Temporary compatibility exports
// TODO: Update consumers to import directly from './domain'
export type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  DomainDiagram as DomainDiagramType
} from './domain';
