/**
 * Node-specific enumerations
 */

export enum DBBlockSubType {
  FIXED_PROMPT = 'fixed_prompt',
  FILE = 'file',
  CODE = 'code',
  API_TOOL = 'api_tool'
}

export enum DBOperation {
  PROMPT = 'prompt',
  READ = 'read',
  WRITE = 'write',
  APPEND = 'append',
  UPDATE = 'update'
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
  HTTP = 'http',
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
  CUSTOM = 'custom',
  LLM_DECISION = 'llm_decision'
}

export enum TemplateEngine {
  INTERNAL = 'internal',
  JINJA2 = 'jinja2'
}

export enum IRBuilderTargetType {
  BACKEND = 'backend',
  FRONTEND = 'frontend',
  STRAWBERRY = 'strawberry',
  CUSTOM = 'custom'
}

export enum IRBuilderSourceType {
  AST = 'ast',
  SCHEMA = 'schema',
  CONFIG = 'config',
  AUTO = 'auto'
}

export enum IRBuilderOutputFormat {
  JSON = 'json',
  YAML = 'yaml',
  PYTHON = 'python'
}

export enum TypeScriptExtractPattern {
  INTERFACE = 'interface',
  TYPE = 'type',
  ENUM = 'enum',
  CLASS = 'class',
  FUNCTION = 'function',
  CONST = 'const',
  EXPORT = 'export'
}

export enum TypeScriptParseMode {
  MODULE = 'module',
  SCRIPT = 'script'
}

export enum TypeScriptOutputFormat {
  STANDARD = 'standard',
  FOR_CODEGEN = 'for_codegen',
  FOR_ANALYSIS = 'for_analysis'
}

export enum DiffFormat {
  UNIFIED = 'unified',
  GIT = 'git',
  CONTEXT = 'context',
  ED = 'ed',
  NORMAL = 'normal'
}

export enum PatchMode {
  NORMAL = 'normal',
  FORCE = 'force',
  DRY_RUN = 'dry_run',
  REVERSE = 'reverse'
}

export enum DataFormat {
  JSON = 'json',
  YAML = 'yaml',
  CSV = 'csv',
  TEXT = 'text',
  XML = 'xml'
}
