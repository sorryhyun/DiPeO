import {
  PersonID,
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

// Re-export from graphql-mappings which provides compatibility layer
export type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  ReactDiagram,
  ArrowData
} from '@/graphql/types/graphql-mappings';

// Node data types - extend domain models with UI-specific properties
export interface StartNodeData extends DomainStartNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface ConditionNodeData extends DomainConditionNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface PersonJobNodeData extends DomainPersonJobNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface EndpointNodeData extends DomainEndpointNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface DBNodeData extends DomainDBNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface JobNodeData extends DomainJobNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface UserResponseNodeData extends DomainUserResponseNodeData {
  flipped?: boolean;
  [key: string]: unknown;
}

export interface NotionNodeData extends DomainNotionNodeData {
  [key: string]: unknown;
}

export interface PersonBatchJobNodeData extends DomainPersonBatchJobNodeData {
  ForgettingMode?: string; // Keep this for backward compatibility
  flipped?: boolean;
  [key: string]: unknown;
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