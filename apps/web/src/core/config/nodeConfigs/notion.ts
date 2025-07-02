import { createUnifiedConfig } from '../unifiedConfig';
import { apolloClient } from '@/graphql/client';
import { GetApiKeysDocument } from '@/__generated__/graphql';

// Define type inline to satisfy constraint
type NotionFormDataType = {
  label?: string;
  operation?: string;
  page_id?: string;
  database_id?: string;
  prompt?: string;
  [key: string]: unknown;
};

export const notionConfig = createUnifiedConfig<NotionFormDataType>({
  // Node configuration
  label: 'Notion',
  icon: '📄',
  color: 'gray',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { 
      name: 'operation', 
      type: 'select', 
      label: 'Operation', 
      required: true,
      options: [
        { value: 'read_page', label: 'Read Page' },
        { value: 'list_blocks', label: 'List Blocks' },
        { value: 'append_blocks', label: 'Append Blocks' },
        { value: 'update_block', label: 'Update Block' },
        { value: 'query_database', label: 'Query Database' },
        { value: 'create_page', label: 'Create Page' },
        { value: 'extract_text', label: 'Extract Text' }
      ]
    },
    { name: 'api_key_id', type: 'string', label: 'API Key', required: true, placeholder: 'Select API key' },
    { name: 'page_id', type: 'string', label: 'Page ID', required: false, placeholder: 'Page ID' },
    { name: 'block_id', type: 'string', label: 'Block ID', required: false, placeholder: 'Block ID' },
    { name: 'database_id', type: 'string', label: 'Database ID', required: false, placeholder: 'Database ID' }
  ],
  defaults: { operation: 'read_page', api_key_id: '', page_id: '', block_id: '', database_id: '', label: '' },
  
  // Panel configuration overrides
  panelLayout: 'single',
  panelFieldOrder: ['label', 'operation', 'api_key_id', 'page_id', 'block_id', 'database_id'],
  panelFieldOverrides: {
    api_key_id: {
      type: 'select',
      options: async () => {
        try {
          const { data } = await apolloClient.query({
            query: GetApiKeysDocument,
            variables: { service: 'notion' },
            fetchPolicy: 'network-only'
          });
          
          return data.apiKeys?.map((key: { id: string; label: string }) => ({
            value: key.id,
            label: key.label || key.id
          })) || [];
        } catch (error) {
          console.error('Failed to load API keys:', error);
          return [];
        }
      },
      placeholder: 'Select Notion API key...'
    },
    page_id: {
      conditional: {
        field: 'operation',
        values: ['read_page', 'list_blocks', 'append_blocks', 'create_page', 'extract_text'],
        operator: 'includes'
      }
    },
    block_id: {
      conditional: {
        field: 'operation',
        values: ['update_block'],
        operator: 'equals'
      }
    },
    database_id: {
      conditional: {
        field: 'operation',
        values: ['query_database'],
        operator: 'equals'
      }
    }
  },
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Node Name',
      placeholder: 'Notion'
    }
  ]
});