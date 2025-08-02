// Import all domain types from centralized location
import {
  StartNodeData,
  ConditionNodeData,
  PersonJobNodeData,
  EndpointNodeData,
  DBNodeData,
  CodeJobNodeData,
  ApiJobNodeData,
  UserResponseNodeData,
  NotionNodeData,
  PersonBatchJobNodeData,
  HookNodeData,
  TemplateJobNodeData,
  JsonSchemaValidatorNodeData,
  TypescriptAstNodeData,
  SubDiagramNodeData,
  IntegratedApiNodeData,
  WithUI
} from './domain';

/**
 * Node type registry mapping node type strings to their domain types
 */
export interface NodeTypeRegistry {
  start: StartNodeData;
  condition: ConditionNodeData;
  person_job: PersonJobNodeData;
  endpoint: EndpointNodeData;
  db: DBNodeData;
  code_job: CodeJobNodeData;
  api_job: ApiJobNodeData;
  user_response: UserResponseNodeData;
  notion: NotionNodeData;
  person_batch_job: PersonBatchJobNodeData;
  hook: HookNodeData;
  template_job: TemplateJobNodeData;
  json_schema_validator: JsonSchemaValidatorNodeData;
  typescript_ast: TypescriptAstNodeData;
  sub_diagram: SubDiagramNodeData;
  integrated_api: IntegratedApiNodeData;
}

/**
 * All available node type keys
 */
export type NodeTypeKey = keyof NodeTypeRegistry;

/**
 * Generic panel form data wrapper
 * Used for partial form data during editing
 */
export type PanelFormData<T extends Record<string, unknown>> = Partial<T> & {
  [key: string]: unknown;
};

/**
 * Type factory that generates UI-augmented types for all node types
 * Uses the WithUI type from domain.ts
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
    'start', 'condition', 'person_job', 'endpoint', 'db',
    'code_job', 'api_job', 'user_response', 'notion', 'person_batch_job', 'hook',
    'template_job', 'json_schema_validator', 'typescript_ast', 'sub_diagram', 'integrated_api'
  ];
  return validKeys.includes(key as NodeTypeKey);
}

// Re-export UI-augmented node data types for backward compatibility
// These now include UI properties like 'flipped'
export type { StartNodeData, ConditionNodeData, PersonJobNodeData, EndpointNodeData,
  DBNodeData, CodeJobNodeData, ApiJobNodeData, UserResponseNodeData,
  NotionNodeData, PersonBatchJobNodeData, HookNodeData, TemplateJobNodeData,
  JsonSchemaValidatorNodeData, TypescriptAstNodeData, SubDiagramNodeData, IntegratedApiNodeData } from './domain';

/**
 * Form data type aliases for backward compatibility
 */
export type StartFormData = NodeFormData<'start'>;
export type ConditionFormData = NodeFormData<'condition'>;
export type PersonJobFormData = NodeFormData<'person_job'>;
export type EndpointFormData = NodeFormData<'endpoint'>;
export type DBFormData = NodeFormData<'db'>;
export type CodeJobFormData = NodeFormData<'code_job'>;
export type ApiJobFormData = NodeFormData<'api_job'>;
export type UserResponseFormData = NodeFormData<'user_response'>;
export type NotionFormData = NodeFormData<'notion'>;
export type PersonBatchJobFormData = NodeFormData<'person_batch_job'>;
export type HookFormData = NodeFormData<'hook'>;
export type TemplateJobFormData = NodeFormData<'template_job'>;
export type JsonSchemaValidatorFormData = NodeFormData<'json_schema_validator'>;
export type TypescriptAstFormData = NodeFormData<'typescript_ast'>;
export type SubDiagramFormData = NodeFormData<'sub_diagram'>;
export type IntegratedApiFormData = NodeFormData<'integrated_api'>;