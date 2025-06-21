import {
  ForgettingMode,
  NodeResult,
  NodeExecutionStatus,
  NodeType,
  StartNodeData as DomainStartNodeData,
  ConditionNodeData as DomainConditionNodeData,
  PersonJobNodeData as DomainPersonJobNodeData,
  EndpointNodeData as DomainEndpointNodeData,
  DBNodeData as DomainDBNodeData,
  JobNodeData as DomainJobNodeData,
  UserResponseNodeData as DomainUserResponseNodeData,
  NotionNodeData as DomainNotionNodeData,
  PersonBatchJobNodeData as DomainPersonBatchJobNodeData
} from "@dipeo/domain-models";

// Re-export GraphQL types for use in core domain
import type {
  Node as DomainNode,
  Arrow as DomainArrow,
  Handle as DomainHandle,
  Person as DomainPerson,
  ApiKey as DomainApiKey,
  DomainDiagramType as ReactDiagram,
  ArrowData
} from '@/graphql/types';

export type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  ReactDiagram,
  ArrowData
};

// Generic UI extension wrapper for domain models
export type WithUI<T> = T & { 
  flipped?: boolean; 
  [key: string]: unknown;
};

// Node data types - extend domain models with UI-specific properties
export interface StartNodeData extends WithUI<DomainStartNodeData> {}
export interface ConditionNodeData extends WithUI<DomainConditionNodeData> {}
export interface PersonJobNodeData extends WithUI<DomainPersonJobNodeData> {}
export interface EndpointNodeData extends WithUI<DomainEndpointNodeData> {}
export interface DBNodeData extends WithUI<DomainDBNodeData> {}
export interface JobNodeData extends WithUI<DomainJobNodeData> {}
export interface UserResponseNodeData extends WithUI<DomainUserResponseNodeData> {}
export interface NotionNodeData extends WithUI<DomainNotionNodeData> {}
export interface PersonBatchJobNodeData extends WithUI<DomainPersonBatchJobNodeData> {
  ForgettingMode?: string; // Keep this for backward compatibility
}

/**
 * Core node data union type
 * Maps node types to their specific data structures
 */
export type NodeData = {
  start: StartNodeData;
  condition: ConditionNodeData;
  person_job: PersonJobNodeData;
  endpoint: EndpointNodeData;
  db: DBNodeData;
  job: JobNodeData;
  user_response: UserResponseNodeData;
  notion: NotionNodeData;
  person_batch_job: PersonBatchJobNodeData;
};

/**
 * Legacy node execution state for backward compatibility.
 * @deprecated Use NodeResult from @dipeo/domain-models instead
 */
export interface NodeExecutionState {
  status: NodeExecutionStatus;
  error?: string;
  timestamp: number; // Keep as number for backward compatibility
  skipReason?: string;
  tokenCount?: number; // Different from canonical tokenUsage
  progress?: string;
}

/**
 * Convert NodeResult to legacy NodeExecutionState
 */
export function fromCanonicalNodeResult(nodeResult: NodeResult): NodeExecutionState {
  return {
    status: nodeResult.status,
    error: nodeResult.error || undefined,
    timestamp: new Date(nodeResult.timestamp).getTime(),
    skipReason: nodeResult.skipReason || undefined,
    tokenCount: nodeResult.tokenUsage?.total,
    progress: nodeResult.progress || undefined,
  };
}

/**
 * Convert legacy NodeExecutionState to NodeResult
 */
export function toCanonicalNodeResult(
  nodeId: string,
  state: NodeExecutionState,
): NodeResult {
  return {
    nodeId: nodeId as any, // NodeID branded type
    status: state.status,
    error: state.error || null,
    timestamp: new Date(state.timestamp).toISOString(),
    skipReason: state.skipReason || null,
    progress: state.progress || null,
    tokenUsage: state.tokenCount ? {
      input: 0,
      output: 0,
      total: state.tokenCount,
    } : null,
  };
}

// Type guards are now imported from graphql-mappings
export { isDomainNode, isReactDiagram } from '@/graphql/types/graphql-mappings';

/**
 * Utility types for working with nodes
 */
export type NodeDataOfType<T extends NodeType> = T extends keyof NodeData ? NodeData[T] : never;

// Export format type for diagram export/import operations
export interface ExportFormat {
  nodes: Array<{
    id: string;
    type: string;
    position: { x: number; y: number };
    data: Record<string, any>;
    displayName?: string;
  }>;
  arrows: Array<{
    id: string;
    source: string;
    target: string;
    data?: Record<string, any>;
  }>;
  handles: Array<{
    id: string;
    nodeId: string;
    name: string;
    direction: string;
    dataType: string;
  }>;
  persons: Array<{
    id: string;
    name: string;
    displayName?: string;
    service: string;
    [key: string]: any;
  }>;
  apiKeys: Array<{
    id: string;
    label: string;
    service: string;
    maskedKey: string;
  }>;
  metadata?: {
    id?: string;
    name?: string;
    description?: string;
    version: string;
    created: string;
    modified: string;
    author?: string;
    tags?: string[];
  };
}