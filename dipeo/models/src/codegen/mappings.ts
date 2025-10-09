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
  'PersonID': 'Optional[PersonID]',
  'NodeID': 'NodeID',
  'HandleID': 'HandleID',
  'ArrowID': 'ArrowID',
  'MemoryConfig': 'Optional[MemoryConfig]',
  'ToolConfig[]': 'Optional[List[ToolConfig]]',
  'string[]': 'Optional[List[str]]',
  'Record<string, any>': 'JsonDict',
  'Record<string, JsonValue>': 'JsonDict',
  'Record<string, string>': 'Dict[str, str]',
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
  'AuthType': 'AuthType'
};

export const TYPE_TO_FIELD: Record<string, string> = {
  'string': 'text',
  'number': 'number',
  'boolean': 'checkbox',
  'PersonID': 'personSelect',
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
  'AuthType': 'select'
};

export const TYPE_TO_ZOD: Record<string, string> = {
  'string': 'z.string()',
  'number': 'z.number()',
  'boolean': 'z.boolean()',
  'any': 'z.unknown()',
  'JsonValue': 'z.unknown()',
  'JsonDict': 'z.record(z.unknown())',
  'PersonID': 'z.string()',
  'NodeID': 'z.string()',
  'HandleID': 'z.string()',
  'ArrowID': 'z.string()',
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
  'AuthType': 'z.nativeEnum(AuthType)'
};

export const BRANDED_TYPES = [
  'PersonID', 'NodeID', 'HandleID', 'ArrowID', 'NodeType',
  'SupportedLanguage', 'HttpMethod', 'DBBlockSubType', 'DBOperation',
  'HookType', 'HookTriggerMode', 'ContentType',
  'ToolSelection', 'APIServiceType', 'ConditionType', 'TemplateEngine',
  'IRBuilderTargetType', 'IRBuilderSourceType', 'IRBuilderOutputFormat',
  'TypeScriptExtractPattern', 'TypeScriptParseMode', 'TypeScriptOutputFormat',
  'DiffFormat', 'PatchMode', 'AuthType', 'DiagramFormat'
];

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
  BASE_FIELDS,
  FIELD_SPECIAL_HANDLING
};
