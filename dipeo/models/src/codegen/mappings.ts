/**
 * Codegen mappings and configurations
 * Used by the code generation system to map between TypeScript and target languages
 */

import { NODE_INTERFACE_MAP } from './node-interface-map.js';

export const TS_TO_PY_TYPE: Record<string, string> = {
  'string': 'str',
  'number': 'int',
  'boolean': 'bool',
  'any': 'JsonValue',
  'JsonValue': 'JsonValue',
  'JsonDict': 'JsonDict',
  // Branded ID types (base types without Optional wrapper)
  'PersonID': 'PersonID',
  'NodeID': 'NodeID',
  'HandleID': 'HandleID',
  'ArrowID': 'ArrowID',
  'ApiKeyID': 'ApiKeyID',
  'DiagramID': 'DiagramID',
  'ExecutionID': 'ExecutionID',
  'FileID': 'FileID',
  // Other complex types
  'MemoryConfig': 'Optional[MemoryConfig]',
  'ToolConfig[]': 'Optional[List[ToolConfig]]',
  'string[]': 'Optional[List[str]]',
  'Record<string, any>': 'JsonDict',
  'Record<string, JsonValue>': 'JsonDict',
  'Record<string, string>': 'Dict[str, str]',
  // Enum types
  'HookTriggerMode': 'Optional[HookTriggerMode]',
  'SupportedLanguage': 'SupportedLanguage',
  'HttpMethod': 'HttpMethod',
  'DBBlockSubType': 'DBBlockSubType',
  'DBOperation': 'DBOperation',
  'HookType': 'HookType',
  'DiagramFormat': 'DiagramFormat',
  'ContentType': 'ContentType',
  'ToolSelection': 'ToolSelection',
  'APIServiceType': 'APIServiceType',
  'ConditionType': 'ConditionType',
  'TemplateEngine': 'TemplateEngine',
  'IRBuilderTargetType': 'IRBuilderTargetType',
  'IRBuilderSourceType': 'IRBuilderSourceType',
  'IRBuilderOutputFormat': 'IRBuilderOutputFormat',
  'TypeScriptExtractPattern': 'TypeScriptExtractPattern',
  'TypeScriptParseMode': 'TypeScriptParseMode',
  'TypeScriptOutputFormat': 'TypeScriptOutputFormat',
  'DiffFormat': 'DiffFormat',
  'PatchMode': 'PatchMode',
  'AuthType': 'AuthType',
  'DataFormat': 'DataFormat',
  // Array types
  'number[]': 'Optional[List[int]]',
  'boolean[]': 'Optional[List[bool]]',
  'any[]': 'Optional[List[JsonValue]]',
  // Object types
  'object': 'JsonDict'
};

export const TYPE_TO_FIELD: Record<string, string> = {
  'string': 'text',
  'number': 'number',
  'boolean': 'checkbox',
  // Branded ID types - special UI components
  'PersonID': 'personSelect',
  'NodeID': 'nodeSelect',
  'HandleID': 'text',
  'ArrowID': 'text',
  'ApiKeyID': 'apiKeySelect',
  'DiagramID': 'diagramSelect',
  'ExecutionID': 'text',
  'FileID': 'fileSelect',
  // Enum types - select dropdowns
  'SupportedLanguage': 'select',
  'HttpMethod': 'select',
  'DBBlockSubType': 'select',
  'DBOperation': 'select',
  'HookType': 'select',
  'HookTriggerMode': 'select',
  'ContentType': 'select',
  'DiagramFormat': 'select',
  'ToolSelection': 'select',
  'APIServiceType': 'select',
  'ConditionType': 'select',
  'TemplateEngine': 'select',
  'IRBuilderTargetType': 'select',
  'IRBuilderSourceType': 'select',
  'IRBuilderOutputFormat': 'select',
  'TypeScriptExtractPattern': 'select',
  'TypeScriptParseMode': 'select',
  'TypeScriptOutputFormat': 'select',
  'DiffFormat': 'select',
  'PatchMode': 'select',
  'AuthType': 'select',
  'DataFormat': 'select',
  // Array types
  'string[]': 'array',
  'number[]': 'array',
  'any[]': 'array',
  // Object types
  'object': 'code'
};

export const TYPE_TO_ZOD: Record<string, string> = {
  'string': 'z.string()',
  'number': 'z.number()',
  'boolean': 'z.boolean()',
  'any': 'z.unknown()',
  'JsonValue': 'z.unknown()',
  'JsonDict': 'z.record(z.unknown())',
  // Branded ID types (all serialize as strings)
  'PersonID': 'z.string()',
  'NodeID': 'z.string()',
  'HandleID': 'z.string()',
  'ArrowID': 'z.string()',
  'ApiKeyID': 'z.string()',
  'DiagramID': 'z.string()',
  'ExecutionID': 'z.string()',
  'FileID': 'z.string()',
  // Enum types
  'SupportedLanguage': 'z.nativeEnum(SupportedLanguage)',
  'HttpMethod': 'z.nativeEnum(HttpMethod)',
  'DBBlockSubType': 'z.nativeEnum(DBBlockSubType)',
  'DBOperation': 'z.nativeEnum(DBOperation)',
  'HookType': 'z.nativeEnum(HookType)',
  'HookTriggerMode': 'z.nativeEnum(HookTriggerMode)',
  'ContentType': 'z.nativeEnum(ContentType)',
  'NodeType': 'z.nativeEnum(NodeType)',
  'DiagramFormat': 'z.nativeEnum(DiagramFormat)',
  'ToolSelection': 'z.nativeEnum(ToolSelection)',
  'APIServiceType': 'z.nativeEnum(APIServiceType)',
  'ConditionType': 'z.nativeEnum(ConditionType)',
  'TemplateEngine': 'z.nativeEnum(TemplateEngine)',
  'IRBuilderTargetType': 'z.nativeEnum(IRBuilderTargetType)',
  'IRBuilderSourceType': 'z.nativeEnum(IRBuilderSourceType)',
  'IRBuilderOutputFormat': 'z.nativeEnum(IRBuilderOutputFormat)',
  'TypeScriptExtractPattern': 'z.nativeEnum(TypeScriptExtractPattern)',
  'TypeScriptParseMode': 'z.nativeEnum(TypeScriptParseMode)',
  'TypeScriptOutputFormat': 'z.nativeEnum(TypeScriptOutputFormat)',
  'DiffFormat': 'z.nativeEnum(DiffFormat)',
  'PatchMode': 'z.nativeEnum(PatchMode)',
  'AuthType': 'z.nativeEnum(AuthType)',
  'DataFormat': 'z.nativeEnum(DataFormat)',
  // Array types
  'string[]': 'z.array(z.string())',
  'number[]': 'z.array(z.number())',
  'boolean[]': 'z.array(z.boolean())',
  'any[]': 'z.array(z.any())',
  // Object types
  'object': 'z.record(z.any())'
};

// Branded types (ID types with compile-time type safety)
export const BRANDED_ID_TYPES = [
  'PersonID', 'NodeID', 'HandleID', 'ArrowID', 'ApiKeyID',
  'DiagramID', 'ExecutionID', 'FileID'
];

// Enum types (used for field validation and type safety)
export const ENUM_TYPES = [
  'NodeType', 'SupportedLanguage', 'HttpMethod', 'DBBlockSubType', 'DBOperation',
  'HookType', 'HookTriggerMode', 'ContentType', 'ToolSelection', 'APIServiceType',
  'ConditionType', 'TemplateEngine', 'IRBuilderTargetType', 'IRBuilderSourceType',
  'IRBuilderOutputFormat', 'TypeScriptExtractPattern', 'TypeScriptParseMode',
  'TypeScriptOutputFormat', 'DiffFormat', 'PatchMode', 'AuthType', 'DiagramFormat',
  'DataFormat'
];

// Combined list for backward compatibility
export const BRANDED_TYPES = [...BRANDED_ID_TYPES, ...ENUM_TYPES];

export const BASE_FIELDS = ['label', 'flipped'];

export const FIELD_SPECIAL_HANDLING: Record<string, Record<string, any>> = {
  'person_job': {
    'person': { py_name: 'person_id' },
    'first_only_prompt': { default: '""' },
    'memory_config': { special: 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None' },
    'tools': { special: '[ToolConfig(**tool) if isinstance(tool, dict) else tool for tool in data.get("tools", [])] if data.get("tools") else None' }
  },
  'start': {
    'custom_data': { default: 'field(default_factory=dict)' },
    'output_data_structure': { default: 'field(default_factory=dict)' }
  },
  'endpoint': {
    'save_to_file': { default: 'False' }
  },
  'condition': {
    'condition_type': { default: '""' }
  },
  'code_job': {
    'language': { default: 'field(default=SupportedLanguage.python)' }
  },
  'api_job': {
    'url': { default: '""' },
    'method': { default: 'field(default=HttpMethod.GET)' }
  },
  'db': {
    'sub_type': { default: 'field(default=DBBlockSubType.fixed_prompt)' },
    'operation': { default: '""' }
  },
  'user_response': {
    'prompt': { default: '""' },
    'timeout': { default: '60' }
  },
  'hook': {
    'hook_type': { default: 'field(default=HookType.shell)' },
    'config': { default: 'field(default_factory=dict)' }
  },
  'template_job': {
    'template_type': { default: '"jinja2"' },
    'merge_source': { default: '"default"' }
  },
  'json_schema_validator': {
    'strict_mode': { default: 'False' },
    'error_on_extra': { default: 'False' }
  },
  'typescript_ast': {
    'extract_patterns': { default: 'field(default_factory=lambda: ["interface", "type", "enum"])' },
    'include_jsdoc': { default: 'False' },
    'parse_mode': { default: '"module"' }
  },
  'sub_diagram': {
    'batch': { default: 'False' },
    'batch_input_key': { default: '"items"' },
    'batch_parallel': { default: 'True' }
  },
  'integrated_api': {
    'provider': { default: 'field(default=APIServiceType.NOTION)' },
    'operation': { default: '""' },
    'timeout': { default: '30' },
    'max_retries': { default: '3' },
    'config': { default: 'field(default_factory=dict)' }
  }
};

export const CODEGEN_MAPPINGS = {
  NODE_INTERFACE_MAP,
  TS_TO_PY_TYPE,
  TYPE_TO_FIELD,
  TYPE_TO_ZOD,
  BRANDED_TYPES,
  BRANDED_ID_TYPES,
  ENUM_TYPES,
  BASE_FIELDS,
  FIELD_SPECIAL_HANDLING
};
