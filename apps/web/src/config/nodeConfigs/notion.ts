import type { NodeConfigItem } from '@/types/config';

export const notionNodeConfig: NodeConfigItem = {
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
    { name: 'apiKeyId', type: 'string', label: 'API Key', required: true, placeholder: 'Select API key...' },
    { name: 'pageId', type: 'string', label: 'Page ID', placeholder: 'Notion page ID' },
    { name: 'blockId', type: 'string', label: 'Block ID', placeholder: 'Notion block ID' },
    { name: 'databaseId', type: 'string', label: 'Database ID', placeholder: 'Notion database ID' }
  ],
  defaults: { operation: 'read_page', apiKeyId: '', pageId: '', blockId: '', databaseId: '' }
};