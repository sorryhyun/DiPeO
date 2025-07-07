import type { UnifiedFieldDefinition } from '../field-registry';
import type { NotionNodeData } from '@/core/types';

export const notionFields: UnifiedFieldDefinition<NotionNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter Notion label'
  },
  {
    name: 'api_key',
    type: 'text',
    label: 'API Key',
    required: true,
    placeholder: 'Your Notion API key'
  },
  {
    name: 'database_id',
    type: 'text',
    label: 'Database ID',
    required: true,
    placeholder: 'Notion database ID'
  },
  {
    name: 'operation',
    type: 'select',
    label: 'Operation',
    required: true,
    options: [
      { value: 'query', label: 'Query Database' },
      { value: 'create', label: 'Create Page' },
      { value: 'update', label: 'Update Page' }
    ]
  }
];