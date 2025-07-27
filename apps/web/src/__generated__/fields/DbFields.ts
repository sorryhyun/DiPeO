// Generated field configuration for db
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const dbFields: UnifiedFieldDefinition[] = [
  {
    name: 'collection',
    type: 'text',
    label: 'Collection',
    required: false,
    description: 'Collection configuration',
  },
  {
    name: 'data',
    type: 'code',
    label: 'Data',
    required: false,
    description: 'Data configuration',
  },
  {
    name: 'file',
    type: 'text',
    label: 'File',
    required: false,
    description: 'File configuration',
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
    name: 'sub_type',
    type: 'select',
    label: 'Sub Type',
    required: true,
    description: 'Sub Type configuration',
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
];