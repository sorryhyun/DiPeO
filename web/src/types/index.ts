// types/index.ts - Central export point for all types
// Provides backward compatibility during migration

// Core types - now from core/types
export * from '@/core/types';

// Feature-specific types
export * from '@/features/diagram-editor/types';
export * from '@/features/execution-monitor/types';
export * from '@/features/properties-editor/types';

// Shared types
export * from '@/shared/types';

// GraphQL types - selectively export to avoid conflicts
export {
  domainToReactDiagram,
  diagramToStoreMaps,
  nodeKindToGraphQLType,
  graphQLTypeToNodeKind,
  getNodeHandles,
  areHandlesCompatible,
  isDomainNode,
  isReactDiagram,
  createEmptyDiagram
} from '@/graphql/types';

// Export React Flow types and adapters from DiagramAdapter
export type {
  ReactFlowDiagram,
  DiPeoNode,
  DiPeoEdge,
  ValidatedConnection,
  DiPeoReactInstance
} from '@/features/diagram-editor/adapters/DiagramAdapter';

export {
  isDiPeoNode,
  isDiPeoEdge,
  nodeToReact,
  arrowToReact,
  diagramToReact,
  reactToNode,
  reactToArrow,
  connectionToArrow,
  validateConnection,
  DiagramAdapter
} from '@/features/diagram-editor/adapters/DiagramAdapter';

// Note: Branded types are now re-exported from @/core/types
// GraphQL mappings are now re-exported from @/graphql/types
// Node kinds are now re-exported from @/features/diagram-editor/types
export type {
  Node,
  Arrow,
  Handle,
  Person,
  ApiKey,
  Diagram,
  ExecutionStatus,
  EventType
} from '@/__generated__/graphql';

// Export enums as both types and values
export {
  NodeType,
  LlmService,
  ForgettingMode
} from '@/__generated__/graphql';