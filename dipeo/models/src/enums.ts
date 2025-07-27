/**
 * Shared enum definitions for diagram-related types
 * These enums are used by both frontend and backend via code generation
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
  NOTION = 'notion',
  PERSON_BATCH_JOB = 'person_batch_job',
  HOOK = 'hook',
  TEMPLATE_JOB = 'template_job',
  JSON_SCHEMA_VALIDATOR = 'json_schema_validator',
  TYPESCRIPT_AST = 'typescript_ast',
  SUB_DIAGRAM = 'sub_diagram'
}

export enum HandleDirection {
  INPUT = 'input',
  OUTPUT = 'output'
}

export enum HandleLabel {
  DEFAULT = 'default',
  FIRST = 'first',
  CONDITION_TRUE = 'condtrue',
  CONDITION_FALSE = 'condfalse',
  SUCCESS = 'success',
  ERROR = 'error',
  RESULTS = 'results'
}

export enum DataType {
  ANY = 'any',
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  OBJECT = 'object',
  ARRAY = 'array'
}

export enum MemoryView {
  ALL_INVOLVED = 'all_involved',  // Messages where person is sender or recipient
  SENT_BY_ME = 'sent_by_me',      // Messages I sent
  SENT_TO_ME = 'sent_to_me',      // Messages sent to me
  SYSTEM_AND_ME = 'system_and_me', // System messages and my interactions
  CONVERSATION_PAIRS = 'conversation_pairs', // Request/response pairs
  ALL_MESSAGES = 'all_messages',  // All messages in conversation (for judges/observers)
}

export enum DiagramFormat {
  NATIVE = 'native',
  LIGHT = 'light',
  READABLE = 'readable'
}

export enum DBBlockSubType {
  FIXED_PROMPT = 'fixed_prompt',
  FILE = 'file',
  CODE = 'code',
  API_TOOL = 'api_tool'
}

export enum ContentType {
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state',
  OBJECT = 'object'
}

export enum SupportedLanguage {
  PYTHON = 'python',
  TYPESCRIPT = 'typescript',
  BASH = 'bash',
  SHELL = 'shell'
}

export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH'
}

export enum HookType {
  SHELL = 'shell',
  WEBHOOK = 'webhook',
  PYTHON = 'python',
  FILE = 'file'
}

export enum HookTriggerMode {
  MANUAL = 'manual',
  HOOK = 'hook'
}