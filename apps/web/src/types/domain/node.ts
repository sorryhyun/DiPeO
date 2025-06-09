import { NodeID } from '../branded';
import { Vec2, NodeKind } from '../primitives';

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

export type StartNode = TypedDomainNode<NodeKind.Start, StartNodeData>;

/**
 * Condition node domain model
 */
export interface ConditionNodeData {
  label?: string;
  condition: string;
  detect_max_iterations?: boolean;
  _node_indices?: string[];
  [key: string]: unknown;
}

export type ConditionNode = TypedDomainNode<NodeKind.Condition, ConditionNodeData>;

/**
 * Person job node domain model
 */
export interface PersonJobNodeData {
  label?: string;
  agent?: string;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations?: number;
  no_forget?: boolean;
  forget_on_every_turn?: boolean;
  forget_upon_request?: boolean;
  [key: string]: unknown;
}

export type PersonJobNode = TypedDomainNode<NodeKind.PersonJob, PersonJobNodeData>;

/**
 * Endpoint node domain model
 */
export interface EndpointNodeData {
  label?: string;
  saveToFile?: boolean;
  fileName?: string;
  [key: string]: unknown;
}

export type EndpointNode = TypedDomainNode<NodeKind.Endpoint, EndpointNodeData>;

/**
 * DB node domain model
 */
export interface DBNodeData {
  label?: string;
  file?: string;
  collection?: string;
  operation?: 'query' | 'write' | 'update' | 'delete';
  query?: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export type DBNode = TypedDomainNode<NodeKind.DB, DBNodeData>;

/**
 * Job node domain model
 */
export interface JobNodeData {
  label?: string;
  codeType: 'python' | 'javascript' | 'bash';
  code: string;
  [key: string]: unknown;
}

export type JobNode = TypedDomainNode<NodeKind.Job, JobNodeData>;

/**
 * User response node domain model
 */
export interface UserResponseNodeData {
  label?: string;
  prompt: string;
  timeout?: number;
  [key: string]: unknown;
}

export type UserResponseNode = TypedDomainNode<NodeKind.UserResponse, UserResponseNodeData>;

/**
 * Notion node domain model
 */
export interface NotionNodeData {
  label?: string;
  operation: 'create' | 'read' | 'update';
  pageId?: string;
  databaseId?: string;
  title?: string;
  content?: string;
  properties?: Record<string, unknown>;
  [key: string]: unknown;
}

export type NotionNode = TypedDomainNode<NodeKind.Notion, NotionNodeData>;

/**
 * Person batch job node domain model
 */
export interface PersonBatchJobNodeData {
  label?: string;
  agent?: string;
  process_type: 'batch' | 'sequential';
  basePrompt: string;
  outputStructure: Record<string, string>;
  parallelism?: number;
  [key: string]: unknown;
}

export type PersonBatchJobNode = TypedDomainNode<NodeKind.PersonBatchJob, PersonBatchJobNodeData>;

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