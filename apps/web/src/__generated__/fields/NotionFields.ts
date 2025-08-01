







// Generated field configuration for notion
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const notionFields: UnifiedFieldDefinition[] = [
  {
    name: 'api_key',
    type: 'text',
    label: 'Api Key',
    required: true,
    placeholder: 'Your Notion API key',
    description: 'Notion API key for authentication',
  },
  {
    name: 'database_id',
    type: 'text',
    label: 'Database Id',
    required: true,
    placeholder: 'Notion database ID',
    description: 'Notion database ID',
  },
  {
    name: 'operation',
    type: 'select',
    label: 'Operation',
    required: true,
    description: 'Operation to perform on the database',
    options: [
      { value: 'query', label: 'Query Database' },
      { value: 'create', label: 'Create Page' },
      { value: 'update', label: 'Update Page' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'page_id',
    type: 'text',
    label: 'Page Id',
    required: false,
    placeholder: 'Page ID (required for update)',
    description: 'Page ID for update operations',
  },
];