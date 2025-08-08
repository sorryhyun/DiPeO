/**
 * Node-specific enumerations
 */

export enum DBBlockSubType {
  FIXED_PROMPT = 'fixed_prompt',
  FILE = 'file',
  CODE = 'code',
  API_TOOL = 'api_tool'
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

export enum ConditionType {
  DETECT_MAX_ITERATIONS = 'detect_max_iterations',
  CHECK_NODES_EXECUTED = 'check_nodes_executed',
  CUSTOM = 'custom'
}

export enum TemplateEngine {
  INTERNAL = 'internal',
  JINJA2 = 'jinja2'
}