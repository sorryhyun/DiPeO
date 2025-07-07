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

/**
 * Node type registry mapping node type strings to their domain types
 */
export interface NodeTypeRegistry {
  start: DomainStartNodeData;
  condition: DomainConditionNodeData;
  person_job: DomainPersonJobNodeData;
  endpoint: DomainEndpointNodeData;
  db: DomainDBNodeData;
  job: DomainJobNodeData;
  code_job: DomainCodeJobNodeData;
  api_job: DomainApiJobNodeData;
  user_response: DomainUserResponseNodeData;
  notion: DomainNotionNodeData;
  person_batch_job: DomainPersonBatchJobNodeData;
  hook: DomainHookNodeData;
}

/**
 * All available node type keys
 */
export type NodeTypeKey = keyof NodeTypeRegistry;

/**
 * Generic UI extension wrapper for domain models
 */
export type WithUI<T> = T & { 
  flipped?: boolean; 
  [key: string]: unknown;
};

/**
 * Generic panel form data wrapper
 */
export type PanelFormData<T extends Record<string, unknown>> = Partial<T> & {
  [key: string]: unknown;
};

/**
 * Type factory that generates WithUI types for all node types
 */
export type NodeDataTypes = {
  [K in NodeTypeKey]: WithUI<NodeTypeRegistry[K]>;
};

/**
 * Type factory that generates PanelFormData types for all node types
 */
export type NodeFormDataTypes = {
  [K in NodeTypeKey]: PanelFormData<NodeDataTypes[K]>;
};

/**
 * Helper type to extract a specific node data type
 */
export type NodeData<K extends NodeTypeKey> = NodeDataTypes[K];

/**
 * Helper type to extract a specific node form data type
 */
export type NodeFormData<K extends NodeTypeKey> = NodeFormDataTypes[K];

/**
 * Type guard to check if a key is a valid node type
 */
export function isNodeTypeKey(key: string): key is NodeTypeKey {
  const validKeys: NodeTypeKey[] = [
    'start', 'condition', 'person_job', 'endpoint', 'db', 'job',
    'code_job', 'api_job', 'user_response', 'notion', 'person_batch_job', 'hook'
  ];
  return validKeys.includes(key as NodeTypeKey);
}

/**
 * Type alias for backward compatibility
 */
export type StartNodeData = NodeData<'start'>;
export type ConditionNodeData = NodeData<'condition'>;
export type PersonJobNodeData = NodeData<'person_job'>;
export type EndpointNodeData = NodeData<'endpoint'>;
export type DBNodeData = NodeData<'db'>;
export type JobNodeData = NodeData<'job'>;
export type CodeJobNodeData = NodeData<'code_job'>;
export type ApiJobNodeData = NodeData<'api_job'>;
export type UserResponseNodeData = NodeData<'user_response'>;
export type NotionNodeData = NodeData<'notion'>;
export type PersonBatchJobNodeData = NodeData<'person_batch_job'>;
export type HookNodeData = NodeData<'hook'>;

/**
 * Form data type aliases for backward compatibility
 */
export type StartFormData = NodeFormData<'start'>;
export type ConditionFormData = NodeFormData<'condition'>;
export type PersonJobFormData = NodeFormData<'person_job'>;
export type EndpointFormData = NodeFormData<'endpoint'>;
export type DBFormData = NodeFormData<'db'>;
export type JobFormData = NodeFormData<'job'>;
export type CodeJobFormData = NodeFormData<'code_job'>;
export type ApiJobFormData = NodeFormData<'api_job'>;
export type UserResponseFormData = NodeFormData<'user_response'>;
export type NotionFormData = NodeFormData<'notion'>;
export type PersonBatchJobFormData = NodeFormData<'person_batch_job'>;
export type HookFormData = NodeFormData<'hook'>;