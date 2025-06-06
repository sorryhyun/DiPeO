import type { PanelConfig } from '@/types';

export const notionPanelConfig: PanelConfig<Record<string, any>> = {
  layout: 'single',
  fields: [
    {
      name: 'label',
      label: 'Label',
      type: 'text',
      placeholder: 'Notion'
    },
    {
      name: 'operation',
      label: 'Operation',
      type: 'select',
      options: [
        { value: 'read_page', label: 'Read Page' },
        { value: 'list_blocks', label: 'List Blocks' },
        { value: 'append_blocks', label: 'Append Blocks' },
        { value: 'update_block', label: 'Update Block' },
        { value: 'query_database', label: 'Query Database' },
        { value: 'create_page', label: 'Create Page' },
        { value: 'extract_text', label: 'Extract Text from Blocks' }
      ]
    },
    {
      name: 'apiKeyId',
      label: 'API Key',
      type: 'select',
      options: []
    },
    {
      name: 'pageId',
      label: 'Page ID',
      type: 'text',
      placeholder: 'Enter Notion page ID (e.g., 202c8edd335e8059af75fe79d0451885)',
      conditional: {
        field: 'operation',
        values: ['read_page', 'list_blocks', 'append_blocks']
      }
    },
    {
      name: 'blockId',
      label: 'Block ID',
      type: 'text',
      placeholder: 'Enter block ID',
      conditional: {
        field: 'operation',
        values: ['update_block']
      }
    },
    {
      name: 'databaseId',
      label: 'Database ID',
      type: 'text',
      placeholder: 'Enter database ID',
      conditional: {
        field: 'operation',
        values: ['query_database']
      }
    }
  ]
};