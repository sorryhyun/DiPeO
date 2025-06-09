import { NodeID } from '../branded';
import { Vec2, NodeKind, ConditionType, PersonForgettingStrategy, JobLanguage, DBOperation, DBSubType, NotionOperation, ProcessType } from '../primitives';

/**
 * Pure domain node - framework-agnostic representation
 * No React Flow or UI framework dependencies
 */
export interface DomainNode {
  id: NodeID;
  type: NodeKind;
  position: Vec2;
  data: Record<string, unknown>;
}

/**
 * Node with typed data for specific node types
 */
export interface TypedDomainNode<T extends NodeKind, D extends Record<string, unknown> = Record<string, unknown>>
  extends DomainNode {
  type: T;
  data: D;
}

/**
 * Start node domain model
 */
export interface StartNodeData {
  label?: string;
  customData: Record<string, unknown>;
  outputDataStructure: Record<string, string>;
  [key: string]: unknown;
}

export type StartNode = TypedDomainNode<NodeKind, StartNodeData> & { type: 'start' };

/**
 * Condition node domain model
 */
export interface ConditionNodeData {
  label?: string;
  conditionType?: ConditionType;
  detect_max_iterations?: boolean;
  expression?: string;
  _node_indices?: string[];
  [key: string]: unknown;
}

export type ConditionNode = TypedDomainNode<NodeKind, ConditionNodeData> & { type: 'condition' };

/**
 * Person job node domain model
 */
export interface PersonJobNodeData {
  label?: string;
  agent?: string;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations?: number;
  contextCleaningRule?: PersonForgettingStrategy;
  [key: string]: unknown;
}

export type PersonJobNode = TypedDomainNode<NodeKind, PersonJobNodeData> & { type: 'person_job' };

/**
 * Endpoint node domain model
 */
export interface EndpointNodeData {
  label?: string;
  saveToFile?: boolean;
  fileName?: string;
  [key: string]: unknown;
}

export type EndpointNode = TypedDomainNode<NodeKind, EndpointNodeData> & { type: 'endpoint' };

/**
 * DB node domain model
 */
export interface DBNodeData {
  label?: string;
  file?: string;
  collection?: string;
  subType?: DBSubType;
  operation?: DBOperation;
  query?: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export type DBNode = TypedDomainNode<NodeKind, DBNodeData> & { type: 'db' };

/**
 * Job node domain model
 */
export interface JobNodeData {
  label?: string;
  codeType: JobLanguage;
  code: string;
  [key: string]: unknown;
}

export type JobNode = TypedDomainNode<NodeKind, JobNodeData> & { type: 'job' };

/**
 * User response node domain model
 */
export interface UserResponseNodeData {
  label?: string;
  prompt: string;
  timeout?: number;
  [key: string]: unknown;
}

export type UserResponseNode = TypedDomainNode<NodeKind, UserResponseNodeData> & { type: 'user_response' };

/**
 * Notion node domain model
 */
export interface NotionNodeData {
  label?: string;
  operation: NotionOperation | 'create' | 'update';
  pageId?: string;
  databaseId?: string;
  title?: string;
  content?: string;
  properties?: Record<string, unknown>;
  [key: string]: unknown;
}

export type NotionNode = TypedDomainNode<NodeKind, NotionNodeData> & { type: 'notion' };

/**
 * Person batch job node domain model
 */
export interface PersonBatchJobNodeData {
  label?: string;
  agent?: string;
  process_type: ProcessType;
  basePrompt: string;
  outputStructure: Record<string, string>;
  contextCleaningRule?: PersonForgettingStrategy;
  parallelism?: number;
  [key: string]: unknown;
}

export type PersonBatchJobNode = TypedDomainNode<NodeKind, PersonBatchJobNodeData> & { type: 'person_batch_job' };

/**
 * Union of all domain node types
 */
export type DiagramNode = 
  | StartNode
  | ConditionNode
  | PersonJobNode
  | EndpointNode
  | DBNode
  | JobNode
  | UserResponseNode
  | NotionNode
  | PersonBatchJobNode;

/**
 * Type guard for domain nodes
 */
export function isDomainNode(obj: unknown): obj is DomainNode {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'type' in obj &&
    'position' in obj &&
    'data' in obj
  );
}

/**
 * Type guard for specific node types
 */
export function isNodeOfKind<T extends NodeKind>(
  node: DomainNode,
  type: T
): node is Extract<DiagramNode, { type: T }> {
  return node.type === type;
}