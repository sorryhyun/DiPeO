/**
 * Type guards for UI-specific types and augmentations
 */

import {
  NodeType,
  type DomainNode,
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
  type HookNodeData,
  type WithUI,
  hasUIProperties
} from './domain';

// Re-export the basic UI properties guard
export { hasUIProperties };

// Node type guards based on NodeType enum
export function isStartNode(node: DomainNode): node is DomainNode & { data: StartNodeData } {
  return node.type === NodeType.START;
}

export function isConditionNode(node: DomainNode): node is DomainNode & { data: ConditionNodeData } {
  return node.type === NodeType.CONDITION;
}

export function isPersonJobNode(node: DomainNode): node is DomainNode & { data: PersonJobNodeData } {
  return node.type === NodeType.PERSON_JOB;
}

export function isEndpointNode(node: DomainNode): node is DomainNode & { data: EndpointNodeData } {
  return node.type === NodeType.ENDPOINT;
}

export function isDBNode(node: DomainNode): node is DomainNode & { data: DBNodeData } {
  return node.type === NodeType.DB;
}

export function isJobNode(node: DomainNode): node is DomainNode & { data: JobNodeData } {
  return node.type === NodeType.JOB;
}

export function isCodeJobNode(node: DomainNode): node is DomainNode & { data: CodeJobNodeData } {
  return node.type === NodeType.CODE_JOB;
}

export function isApiJobNode(node: DomainNode): node is DomainNode & { data: ApiJobNodeData } {
  return node.type === NodeType.API_JOB;
}

export function isUserResponseNode(node: DomainNode): node is DomainNode & { data: UserResponseNodeData } {
  return node.type === NodeType.USER_RESPONSE;
}

export function isNotionNode(node: DomainNode): node is DomainNode & { data: NotionNodeData } {
  return node.type === NodeType.NOTION;
}

export function isPersonBatchJobNode(node: DomainNode): node is DomainNode & { data: PersonBatchJobNodeData } {
  return node.type === NodeType.PERSON_BATCH_JOB;
}

export function isHookNode(node: DomainNode): node is DomainNode & { data: HookNodeData } {
  return node.type === NodeType.HOOK;
}

// UI-augmented node type guard
export function isUINode<T extends DomainNode>(node: T): node is T & { data: WithUI<T['data']> } {
  return hasUIProperties(node.data);
}

// Guards for specific UI states
export function isFlippedNode(node: DomainNode): boolean {
  return hasUIProperties(node.data) && node.data.flipped === true;
}

// Type guard for nodes that can have persons
export function hasPersonConfig(node: DomainNode): node is DomainNode & { 
  data: PersonJobNodeData | PersonBatchJobNodeData 
} {
  return isPersonJobNode(node) || isPersonBatchJobNode(node);
}

// Type guard for nodes that execute code
export function isExecutableNode(node: DomainNode): node is DomainNode & {
  data: JobNodeData | CodeJobNodeData | ApiJobNodeData
} {
  return isJobNode(node) || isCodeJobNode(node) || isApiJobNode(node);
}

// Type guard for nodes with conditions
export function hasConditionLogic(node: DomainNode): node is DomainNode & {
  data: ConditionNodeData
} {
  return isConditionNode(node);
}

// Composite type guard for nodes that interact with external services
export function isExternalServiceNode(node: DomainNode): boolean {
  return isApiJobNode(node) || isNotionNode(node) || isDBNode(node) || hasPersonConfig(node);
}