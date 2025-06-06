import type { PanelConfig } from '@/types';
import { fetchApiKeys } from '@/utils/api';

export const notionPanelConfig: PanelConfig<Record<string, unknown>> = {
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
      options: async () => {
        try {
          const apiKeys = await fetchApiKeys();
          // Filter for Notion API keys only
          return apiKeys
            .filter(key => key.service === 'notion')
            .map(key => ({
              value: key.id,
              label: key.name
            }));
        } catch (error) {
          console.error('Failed to fetch API keys:', error);
          return [];
        }
      }
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