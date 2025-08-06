







// Generated field configuration for notion
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

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
      { value: 'query_database', label: 'Query Database' },
      { value: 'create_page', label: 'Create Page' },
      { value: 'update_page', label: 'Update Page' },
      { value: 'read_page', label: 'Read Page' },
      { value: 'delete_page', label: 'Delete Page' },
      { value: 'create_database', label: 'Create Database' },
      { value: 'update_database', label: 'Update Database' },
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