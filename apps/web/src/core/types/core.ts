import {
  StartNodeData as DomainStartNodeData,
  ConditionNodeData as DomainConditionNodeData,
  PersonJobNodeData as DomainPersonJobNodeData,
  EndpointNodeData as DomainEndpointNodeData,
  DBNodeData as DomainDBNodeData,
  JobNodeData as DomainJobNodeData,
  CodeJobNodeData as DomainCodeJobNodeData,
  ApiJobNodeData as DomainApiJobNodeData,
  UserResponseNodeData as DomainUserResponseNodeData,
  NotionNodeData as DomainNotionNodeData,
  PersonBatchJobNodeData as DomainPersonBatchJobNodeData,
  HookNodeData as DomainHookNodeData
} from "@dipeo/domain-models";

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

// Generic UI extension wrapper for domain models
export type WithUI<T> = T & { 
  flipped?: boolean; 
  [key: string]: unknown;
};

// Node data types - extend domain models with UI-specific properties
export type StartNodeData = WithUI<DomainStartNodeData>;
export type ConditionNodeData = WithUI<DomainConditionNodeData>;
export type PersonJobNodeData = WithUI<DomainPersonJobNodeData>;
export type EndpointNodeData = WithUI<DomainEndpointNodeData>;
export type DBNodeData = WithUI<DomainDBNodeData>;
export type JobNodeData = WithUI<DomainJobNodeData>;
export type CodeJobNodeData = WithUI<DomainCodeJobNodeData>;
export type ApiJobNodeData = WithUI<DomainApiJobNodeData>;
export type UserResponseNodeData = WithUI<DomainUserResponseNodeData>;
export type NotionNodeData = WithUI<DomainNotionNodeData>;
export type PersonBatchJobNodeData = WithUI<DomainPersonBatchJobNodeData>;
export type HookNodeData = WithUI<DomainHookNodeData>;

// Type guards are now imported from graphql-mappings
export { isDomainNode, isDomainDiagram } from '@/graphql/types/graphql-mappings';
