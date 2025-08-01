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
  ALL_INVOLVED = 'all_involved',
  SENT_BY_ME = 'sent_by_me',
  SENT_TO_ME = 'sent_to_me',
  SYSTEM_AND_ME = 'system_and_me',
  CONVERSATION_PAIRS = 'conversation_pairs',
  ALL_MESSAGES = 'all_messages',
}

export enum MemoryProfile {
  FULL = 'FULL',
  FOCUSED = 'FOCUSED',
  MINIMAL = 'MINIMAL',
  GOLDFISH = 'GOLDFISH',
  CUSTOM = 'CUSTOM'
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
  OBJECT = 'object',
  EMPTY = 'empty',
  GENERIC = 'generic',
  VARIABLE = 'variable'
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
  NONE = 'none',
  MANUAL = 'manual',
  HOOK = 'hook'
}

export enum ExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  ABORTED = 'ABORTED',
  SKIPPED = 'SKIPPED'
}

export enum NodeExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  ABORTED = 'ABORTED',
  SKIPPED = 'SKIPPED',
  MAXITER_REACHED = 'MAXITER_REACHED'
}

export enum EventType {
  EXECUTION_STATUS_CHANGED = 'EXECUTION_STATUS_CHANGED',
  NODE_STATUS_CHANGED = 'NODE_STATUS_CHANGED',
  NODE_PROGRESS = 'NODE_PROGRESS',
  INTERACTIVE_PROMPT = 'INTERACTIVE_PROMPT',
  INTERACTIVE_RESPONSE = 'INTERACTIVE_RESPONSE',
  EXECUTION_ERROR = 'EXECUTION_ERROR',
  EXECUTION_UPDATE = 'EXECUTION_UPDATE'
}

export enum LLMService {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GEMINI = 'gemini',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek'
}

export enum APIServiceType {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GEMINI = 'gemini',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek',
  NOTION = 'notion',
  GOOGLE_SEARCH = 'google_search',
  SLACK = 'slack',
  GITHUB = 'github',
  JIRA = 'jira'
}

export enum NotionOperation {
  CREATE_PAGE = 'create_page',
  UPDATE_PAGE = 'update_page',
  READ_PAGE = 'read_page',
  DELETE_PAGE = 'delete_page',
  CREATE_DATABASE = 'create_database',
  QUERY_DATABASE = 'query_database',
  UPDATE_DATABASE = 'update_database'
}

export enum ToolType {
  WEB_SEARCH = 'web_search',
  WEB_SEARCH_PREVIEW = 'web_search_preview',
  IMAGE_GENERATION = 'image_generation'
}

export enum ToolSelection {
  NONE = 'none',
  IMAGE = 'image', 
  WEBSEARCH = 'websearch'
}