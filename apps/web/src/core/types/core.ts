// Re-export node data types from type factories
export {
  type NodeTypeRegistry,
  type NodeTypeKey,
  type WithUI,
  type NodeDataTypes,
  type NodeData,
  isNodeTypeKey,
  // Individual node data types for backward compatibility
  type StartNodeData,
  type ConditionNodeData,
  type PersonJobNodeData,
  type EndpointNodeData,
  type DBNodeData,
  type JobNodeData,
  type CodeJobNodeData,
  type ApiJobNodeData,
  type UserResponseNodeData,
  type NotionNodeData,
  type PersonBatchJobNodeData,
  type HookNodeData
} from './type-factories';

// Re-export GraphQL types for use in core domain
import type {
  Node as DomainNode,
  Arrow as DomainArrow,
  Handle as DomainHandle,
  Person as DomainPerson,
  ApiKey as DomainApiKey,
  DomainDiagramType,
  ArrowData
} from '@/graphql/types';

export type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  DomainDiagramType,
  ArrowData
};

// Type guards are now imported from graphql-mappings
export { isDomainNode, isDomainDiagram } from '@/graphql/types/graphql-mappings';
