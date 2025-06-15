import { createUnifiedConfig } from '../unifiedConfig';

// Define type inline to satisfy constraint
type NotionFormDataType = {
  label?: string;
  operation?: string;
  pageId?: string;
  databaseId?: string;
  prompt?: string;
  [key: string]: unknown;
};

/**
 * Unified configuration for Notion node
 * This replaces both the node config and panel config
 */
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
    { name: 'apiKeyId', type: 'string', label: 'API Key', required: true, placeholder: 'Select API key' },
    { name: 'pageId', type: 'string', label: 'Page ID', required: false, placeholder: 'Page ID' },
    { name: 'blockId', type: 'string', label: 'Block ID', required: false, placeholder: 'Block ID' },
    { name: 'databaseId', type: 'string', label: 'Database ID', required: false, placeholder: 'Database ID' }
  ],
  defaults: { operation: 'read_page', apiKeyId: '', pageId: '', blockId: '', databaseId: '', label: '' },
  
  // Panel configuration overrides
  panelLayout: 'single',
  panelFieldOrder: ['label', 'operation', 'apiKeyId', 'pageId', 'blockId', 'databaseId'],
  panelFieldOverrides: {
    apiKeyId: {
      type: 'select',
      options: async () => {
        try {
          // Check if GraphQL should be used
          const useGraphQL = new URLSearchParams(window.location.search).get('useGraphQL') === 'true' ||
                           import.meta.env.VITE_USE_GRAPHQL === 'true';
          
          if (useGraphQL) {
            // For GraphQL, we would need to use Apollo Client directly here
            // Since this is a config file, we can't use hooks
            // This would require refactoring to move the data fetching to the component level
            console.warn('GraphQL support for API key fetching in config requires component-level refactoring');
            // Fall back to REST for now
          }
          
          // REST API call (current implementation)
          const response = await fetch('/api/apikeys');
          const keys = await response.json();
          return keys
            .filter((key: any) => key.type === 'notion')
            .map((key: any) => ({
              value: key.id,
              label: key.name || key.id
            }));
        } catch (error) {
          console.error('Failed to load API keys:', error);
          return [];
        }
      },
      placeholder: 'Select Notion API key...'
    },
    pageId: {
      conditional: {
        field: 'operation',
        values: ['read_page', 'list_blocks', 'append_blocks', 'create_page', 'extract_text'],
        operator: 'includes'
      }
    },
    blockId: {
      conditional: {
        field: 'operation',
        values: ['update_block'],
        operator: 'equals'
      }
    },
    databaseId: {
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