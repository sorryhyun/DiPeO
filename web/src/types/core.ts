/**
 * Core types for DiPeO
 * Single source of truth for all fundamental types
 */

import type { NodeKind } from './primitives/enums';
import type { PersonID } from './branded';

// Re-export from graphql-mappings which provides compatibility layer
export type {
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  DomainDiagram,
  ArrowData
} from './graphql-mappings';

// Node data types - these are still local definitions since GraphQL uses generic JSONScalar
export interface StartNodeData {
  label: string;
  customData: { [key: string]: string | number | boolean };
  outputDataStructure: { [key: string]: string };
  flipped?: boolean;
  [key: string]: unknown;
}

export interface ConditionNodeData {
  label: string;
  conditionType: string;
  detect_max_iterations: boolean;
  expression?: string;
  _node_indices?: string[];
  flipped?: boolean;
  [key: string]: unknown;
}

export interface PersonJobNodeData {
  label: string;
  person?: PersonID;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations: number;
  contextCleaningRule?: string;
  flipped?: boolean;
  [key: string]: unknown;
}

export interface EndpointNodeData {
  label: string;
  saveToFile: boolean;
  fileName?: string;
  flipped?: boolean;
  [key: string]: unknown;
}

export interface DBNodeData {
  label: string;
  file?: string;
  collection?: string;
  subType: string;
  operation: string;
  query?: string;
  data?: { [key: string]: any };
  flipped?: boolean;
  [key: string]: unknown;
}

export interface JobNodeData {
  label: string;
  codeType: string;
  code: string;
  flipped?: boolean;
  [key: string]: unknown;
}

export interface UserResponseNodeData {
  label: string;
  prompt: string;
  timeout: number;
  flipped?: boolean;
  [key: string]: unknown;
}

export interface NotionNodeData {
  label: string;
  operation: string;
  pageId?: string;
  databaseId?: string;
  [key: string]: unknown;
}

export interface PersonBatchJobNodeData {
  label: string;
  person?: PersonID;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations: number;
  contextCleaningRule?: string;
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
 * Node execution state
 * Tracks runtime state during diagram execution
 */
export interface NodeExecutionState {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'paused';
  error?: string;
  timestamp: number;
  skipReason?: string;
  tokenCount?: number;
  progress?: string;
}

// Type guards are now imported from graphql-mappings
export { isDomainNode, isDomainDiagram } from './graphql-mappings';

/**
 * Utility types for working with nodes
 */
export type NodeDataOfType<T extends NodeKind> = T extends keyof NodeData ? NodeData[T] : never;

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