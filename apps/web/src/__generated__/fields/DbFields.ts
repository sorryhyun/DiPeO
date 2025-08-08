







// Generated field configuration for db
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const dbFields: UnifiedFieldDefinition[] = [
  {
    name: 'file',
    type: 'text',
    label: 'File',
    required: false,
    description: 'File path or array of file paths',
  },
  {
    name: 'collection',
    type: 'text',
    label: 'Collection',
    required: false,
    description: 'Database collection name',
  },
  {
    name: 'sub_type',
    type: 'select',
    label: 'Sub Type',
    required: true,
    description: 'Database operation type',
    options: [
      { value: 'fixed_prompt', label: 'Fixed Prompt' },
      { value: 'file', label: 'File' },
      { value: 'code', label: 'Code' },
      { value: 'api_tool', label: 'API Tool' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'operation',
    type: 'text',
    label: 'Operation',
    required: true,
    description: 'Operation configuration',
  },
  {
    name: 'query',
    type: 'text',
    label: 'Query',
    required: false,
    description: 'Query configuration',
  },
  {
    name: 'data',
    type: 'code',
    label: 'Data',
    required: false,
    description: 'Data configuration',
  },
  {
    name: 'serialize_json',
    type: 'checkbox',
    label: 'Serialize Json',
    required: false,
    defaultValue: false,
    description: 'Serialize structured data to JSON string (for backward compatibility)',
  },
  {
    name: 'format',
    type: 'select',
    label: 'Format',
    required: false,
    defaultValue: "json",
    description: 'Data format (json, yaml, csv, text, etc.)',
    options: [
      { value: 'json', label: 'JSON' },
      { value: 'yaml', label: 'YAML' },
      { value: 'csv', label: 'CSV' },
      { value: 'text', label: 'Text' },
      { value: 'xml', label: 'XML' },
    ],
  },
];