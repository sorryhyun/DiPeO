/**
 * Node type to interface name mappings
 * Maps node type strings to their corresponding TypeScript interface names
 * Note: These interfaces are now generated from specifications, not manually defined
 */

export const NODE_INTERFACE_MAP: Record<string, string> = {
  'start': 'StartNodeData',
  'person_job': 'PersonJobNodeData',
  'person_batch_job': 'PersonBatchJobNodeData',
  'condition': 'ConditionNodeData',
  'endpoint': 'EndpointNodeData',
  'db': 'DBNodeData',
  'code_job': 'CodeJobNodeData',
  'api_job': 'ApiJobNodeData',
  'user_response': 'UserResponseNodeData',
  'hook': 'HookNodeData',
  'template_job': 'TemplateJobNodeData',
  'json_schema_validator': 'JsonSchemaValidatorNodeData',
  'typescript_ast': 'TypescriptAstNodeData',
  'sub_diagram': 'SubDiagramNodeData',
  'integrated_api': 'IntegratedApiNodeData'
};
