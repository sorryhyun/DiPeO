/**
 * Node type definitions for the DiPeO system
 */

export enum NodeType {
  START = 'start',
  PERSON_JOB = 'person_job',
  CONDITION = 'condition',
  CODE_JOB = 'code_job',
  API_JOB = 'api_job',
  ENDPOINT = 'endpoint',
  DB = 'db',
  USER_RESPONSE = 'user_response',
  HOOK = 'hook',
  TEMPLATE_JOB = 'template_job',
  JSON_SCHEMA_VALIDATOR = 'json_schema_validator',
  TYPESCRIPT_AST = 'typescript_ast',
  SUB_DIAGRAM = 'sub_diagram',
  INTEGRATED_API = 'integrated_api',
  IR_BUILDER = 'ir_builder'
}
