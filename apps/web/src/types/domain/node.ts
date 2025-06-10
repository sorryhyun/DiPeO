import {NodeID, PersonID} from '../branded';
import { Vec2, NodeKind, ConditionType, PersonForgettingStrategy, JobLanguage, DBOperation, DBSubType, NotionOperation, ProcessType } from '../primitives';

export interface DomainNode {
  id: NodeID;
  type: NodeKind;
  position: Vec2;
  data: Record<string, unknown>;
}

export interface TypedDomainNode<T extends NodeKind, D extends Record<string, unknown> = Record<string, unknown>>
  extends DomainNode {
  type: T;
  data: D;
}

export interface StartNodeData {
  label?: string;
  customData: Record<string, unknown>;
  outputDataStructure: Record<string, string>;
  [key: string]: unknown;
}

export type StartNode = TypedDomainNode<NodeKind, StartNodeData> & { type: 'start' };

export interface ConditionNodeData {
  label?: string;
  conditionType?: ConditionType;
  detect_max_iterations?: boolean;
  expression?: string;
  _node_indices?: string[];
  [key: string]: unknown;
}

export type ConditionNode = TypedDomainNode<NodeKind, ConditionNodeData> & { type: 'condition' };

export interface PersonJobNodeData {
  label?: string;
  person?: PersonID;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations?: number;
  contextCleaningRule?: PersonForgettingStrategy;
  [key: string]: unknown;
}

export type PersonJobNode = TypedDomainNode<NodeKind, PersonJobNodeData> & { type: 'person_job' };

export interface EndpointNodeData {
  label?: string;
  saveToFile?: boolean;
  fileName?: string;
  [key: string]: unknown;
}

export type EndpointNode = TypedDomainNode<NodeKind, EndpointNodeData> & { type: 'endpoint' };

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

export interface JobNodeData {
  label?: string;
  codeType: JobLanguage;
  code: string;
  [key: string]: unknown;
}

export type JobNode = TypedDomainNode<NodeKind, JobNodeData> & { type: 'job' };

export interface UserResponseNodeData {
  label?: string;
  prompt: string;
  timeout?: number;
  [key: string]: unknown;
}

export type UserResponseNode = TypedDomainNode<NodeKind, UserResponseNodeData> & { type: 'user_response' };

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

export interface PersonBatchJobNodeData {
  label?: string;
  person?: string;
  process_type: ProcessType;
  basePrompt: string;
  outputStructure: Record<string, string>;
  contextCleaningRule?: PersonForgettingStrategy;
  parallelism?: number;
  [key: string]: unknown;
}

export type PersonBatchJobNode = TypedDomainNode<NodeKind, PersonBatchJobNodeData> & { type: 'person_batch_job' };

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

export function isNodeOfKind<T extends NodeKind>(
  node: DomainNode,
  type: T
): node is Extract<DiagramNode, { type: T }> {
  return node.type === type;
}