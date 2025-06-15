// Shared constants for converter modules

// Format versions
export const JSON_VERSION = '4.0.0'; // Updated from v3.0.0 to v4.0.0 as per TODO.md
export const YAML_VERSION = '1.0';

// YAML configuration
export const YAML_STRINGIFY_OPTIONS = {
  indent: 2,
  lineWidth: 120,
  defaultKeyType: 'PLAIN' as const,
  defaultStringType: 'QUOTE_DOUBLE' as const
};

// Default node configuration values
export const DEFAULT_CONTEXT_CLEANING_RULE = 'upon_request';
export const DEFAULT_MAX_ITERATIONS = 1;
export const DEFAULT_MODE = 'sync';
export const DEFAULT_TIMEOUT_SECONDS = 10;
export const DEFAULT_CONDITION_TYPE = 'expression';
export const DEFAULT_FILE_FORMAT = 'text';
export const DEFAULT_NOTION_SUBTYPE = 'read';
export const DEFAULT_DB_SUBTYPE = 'fixed_prompt';
export const DEFAULT_JOB_SUBTYPE = 'code';

// Default LLM configuration
export const DEFAULT_MODEL = 'gpt-4.1-nano';
export const DEFAULT_SERVICE = 'openai';
export const DEFAULT_ASSISTANT_LABEL = 'Default Assistant';

// Node type defaults
export const NODE_DEFAULTS = {
  start: {
    handles: ['output'],
  },
  condition: {
    handles: ['input', 'true', 'false'],
    conditionType: DEFAULT_CONDITION_TYPE,
  },
  job: {
    handles: ['default', 'code', 'output'],
    subType: DEFAULT_JOB_SUBTYPE,
  },
  endpoint: {
    handles: ['input'],
  },
  person_job: {
    handles: ['default', 'first'],
    maxIterations: DEFAULT_MAX_ITERATIONS,
    mode: DEFAULT_MODE,
  },
  person_batch_job: {
    handles: ['default', 'first', 'update', 'error'],
    mode: DEFAULT_MODE,
    timeout: DEFAULT_TIMEOUT_SECONDS,
  },
  db: {
    handles: ['input', 'output'],
    subType: DEFAULT_DB_SUBTYPE,
    fileFormat: DEFAULT_FILE_FORMAT,
  },
  user_response: {
    handles: ['input', 'user_response'],
    timeout: DEFAULT_TIMEOUT_SECONDS,
  },
  notion: {
    handles: ['input', 'output'],
    subType: DEFAULT_NOTION_SUBTYPE,
  }
} as const;