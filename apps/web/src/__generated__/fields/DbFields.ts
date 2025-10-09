// Generated field configuration for db
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const dbFields: UnifiedFieldDefinition[] = [
  {
    name: 'file',
    type: 'text',
    label: '"File"',
    required: false,
    description: '"File path or array of file paths"',
  },
  {
    name: 'collection',
    type: 'text',
    label: '"Collection"',
    required: false,
    description: '"Database collection name"',
  },
  {
    name: 'sub_type',
    type: 'text',
    label: '"Sub type"',
    required: true,
    description: '"Database operation type"',
    options: [
      { value: '"DBBlockSubType.FIXED_PROMPT"', label: '"Fixed Prompt"' },
      { value: '"DBBlockSubType.FILE"', label: '"File"' },
      { value: '"DBBlockSubType.CODE"', label: '"Code"' },
      { value: '"DBBlockSubType.API_TOOL"', label: '"API Tool"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'operation',
    type: 'text',
    label: '"Operation"',
    required: true,
    description: '"Operation configuration"',
    options: [
      { value: '"DBOperation.PROMPT"', label: '"Prompt"' },
      { value: '"DBOperation.READ"', label: '"Read"' },
      { value: '"DBOperation.WRITE"', label: '"Write"' },
      { value: '"DBOperation.APPEND"', label: '"Append"' },
      { value: '"DBOperation.UPDATE"', label: '"Update"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'query',
    type: 'text',
    label: '"Query"',
    required: false,
    description: '"Query configuration"',
  },
  {
    name: 'keys',
    type: 'password',
    label: '"Keys"',
    required: false,
    placeholder: '"e.g., user.profile.name or key1,key2"',
    description: '"Single key or list of dot-separated keys to target within the JSON payload"',
  },
  {
    name: 'lines',
    type: 'text',
    label: '"Lines"',
    required: false,
    placeholder: '"e.g., 1:120 or 5,10:20"',
    description: '"Line selection or ranges to read (e.g., 1:120 or [\'10:20\'])"',
  },
  {
    name: 'data',
    type: 'textarea',
    label: '"Data"',
    required: false,
    description: '"Data configuration"',
  },
  {
    name: 'serialize_json',
    type: 'checkbox',
    label: '"Serialize json"',
    required: false,
    description: '"Serialize structured data to JSON string (for backward compatibility)"',
  },
  {
    name: 'format',
    type: 'text',
    label: '"Format"',
    required: false,
    description: '"Data format (json, yaml, csv, text, etc.)"',
    options: [
      { value: '"DataFormat.JSON"', label: '"JSON"' },
      { value: '"DataFormat.YAML"', label: '"YAML"' },
      { value: '"DataFormat.CSV"', label: '"CSV"' },
      { value: '"DataFormat.TEXT"', label: '"Text"' },
      { value: '"DataFormat.XML"', label: '"XML"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];
