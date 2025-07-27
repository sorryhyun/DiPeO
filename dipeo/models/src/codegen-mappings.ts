/**
 * Codegen mappings and configurations
 * Used by the code generation system to map between TypeScript and target languages
 */

// Node type to interface name mapping
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
  'notion': 'NotionNodeData',
  'hook': 'HookNodeData',
  'template_job': 'TemplateJobNodeData',
  'json_schema_validator': 'JsonSchemaValidatorNodeData',
  'typescript_ast': 'TypescriptAstNodeData',
  'sub_diagram': 'SubDiagramNodeData'
};

// TypeScript to Python type mappings
export const TS_TO_PY_TYPE: Record<string, string> = {
  'string': 'str',
  'number': 'int',
  'boolean': 'bool',
  'any': 'Any',
  'PersonID': 'Optional[PersonID]',
  'NodeID': 'NodeID',
  'HandleID': 'HandleID',
  'ArrowID': 'ArrowID',
  'MemoryConfig': 'Optional[MemoryConfig]',
  'MemorySettings': 'Optional[MemorySettings]',
  'ToolConfig[]': 'Optional[List[ToolConfig]]',
  'string[]': 'Optional[List[str]]',
  'Record<string, any>': 'Dict[str, Any]',
  'Record<string, string>': 'Dict[str, str]',
  'HookTriggerMode': 'Optional[HookTriggerMode]',
  'SupportedLanguage': 'SupportedLanguage',
  'HttpMethod': 'HttpMethod',
  'DBBlockSubType': 'DBBlockSubType',
  'NotionOperation': 'NotionOperation',
  'HookType': 'HookType',
  'DiagramFormat': 'DiagramFormat',
  'ForgettingMode': 'ForgettingMode',
  'ContentType': 'ContentType',
  'MemoryView': 'MemoryView'
};

// Type to UI field type mapping
export const TYPE_TO_FIELD: Record<string, string> = {
  'string': 'text',
  'number': 'number',
  'boolean': 'checkbox',
  'PersonID': 'personSelect',
  'SupportedLanguage': 'select',
  'HttpMethod': 'select',
  'DBBlockSubType': 'select',
  'HookType': 'select',
  'ForgettingMode': 'select',
  'NotionOperation': 'select',
  'HookTriggerMode': 'select',
  'ContentType': 'select',
  'MemoryView': 'select',
  'DiagramFormat': 'select'
};

// Type to Zod schema mapping
export const TYPE_TO_ZOD: Record<string, string> = {
  'string': 'z.string()',
  'number': 'z.number()',
  'boolean': 'z.boolean()',
  'any': 'z.any()',
  'PersonID': 'z.string()',
  'NodeID': 'z.string()',
  'HandleID': 'z.string()',
  'ArrowID': 'z.string()',
  'SupportedLanguage': 'z.nativeEnum(SupportedLanguage)',
  'HttpMethod': 'z.nativeEnum(HttpMethod)',
  'DBBlockSubType': 'z.nativeEnum(DBBlockSubType)',
  'HookType': 'z.nativeEnum(HookType)',
  'ForgettingMode': 'z.nativeEnum(ForgettingMode)',
  'NotionOperation': 'z.nativeEnum(NotionOperation)',
  'HookTriggerMode': 'z.nativeEnum(HookTriggerMode)',
  'ContentType': 'z.nativeEnum(ContentType)',
  'NodeType': 'z.nativeEnum(NodeType)',
  'MemoryView': 'z.nativeEnum(MemoryView)',
  'DiagramFormat': 'z.nativeEnum(DiagramFormat)'
};

// Branded types that shouldn't be generated as schemas
export const BRANDED_TYPES = [
  'PersonID', 'NodeID', 'HandleID', 'ArrowID', 'NodeType',
  'SupportedLanguage', 'HttpMethod', 'DBBlockSubType', 
  'HookType', 'ForgettingMode', 'NotionOperation',
  'HookTriggerMode', 'ContentType', 'MemoryView'
];

// Base fields to skip in generation
export const BASE_FIELDS = ['label', 'flipped'];

// Field special handling configurations for Python generation
export const FIELD_SPECIAL_HANDLING: Record<string, Record<string, any>> = {
  'person_job': {
    'person': { py_name: 'person_id' },
    'first_only_prompt': { default: '""' },
    'max_iteration': { default: '1' },
    'memory_config': { special: 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None' },
    'memory_settings': { special: 'MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None' },
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
  'notion': {
    'operation': { default: 'field(default=NotionOperation.read_page)' }
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
    'extractPatterns': { default: 'field(default_factory=lambda: ["interface", "type", "enum"])' },
    'includeJSDoc': { default: 'False' },
    'parseMode': { default: '"module"' }
  },
  'sub_diagram': {
    'batch': { default: 'False' },
    'batch_input_key': { default: '"items"' },
    'batch_parallel': { default: 'True' }
  }
};

// Export all mappings as a single object for easy access
export const CODEGEN_MAPPINGS = {
  NODE_INTERFACE_MAP,
  TS_TO_PY_TYPE,
  TYPE_TO_FIELD,
  TYPE_TO_ZOD,
  BRANDED_TYPES,
  BASE_FIELDS,
  FIELD_SPECIAL_HANDLING
};