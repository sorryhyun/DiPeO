import { PanelConfig } from '@/types';

const notionConfig: PanelConfig<Record<string, any>> = {
  layout: 'single',
  fields: [
    {
      name: 'label',
      label: 'Label',
      type: 'text',
      placeholder: 'Notion',
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
      ],
    },
    {
      name: 'apiKeyId',
      label: 'API Key',
      type: 'select',
      options: [], // Will be populated dynamically
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
    },
    {
      name: 'blocks',
      label: 'Blocks (JSON)',
      type: 'textarea',
      rows: 6,
      placeholder: `[
  {
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {
          "type": "text",
          "text": {"content": "Hello, {{name}}!"}
        }
      ]
    }
  }
]`,
      conditional: {
        field: 'operation',
        values: ['append_blocks']
      }
    },
    {
      name: 'blockData',
      label: 'Block Data (JSON)',
      type: 'textarea',
      rows: 4,
      placeholder: `{
  "paragraph": {
    "rich_text": [
      {
        "type": "text",
        "text": {"content": "Updated text: {{result}}"}
      }
    ]
  }
}`,
      conditional: {
        field: 'operation',
        values: ['update_block']
      }
    },
    {
      name: 'filter',
      label: 'Filter (JSON)',
      type: 'textarea',
      rows: 4,
      placeholder: `{
  "property": "Status",
  "select": {
    "equals": "Active"
  }
}`,
      conditional: {
        field: 'operation',
        values: ['query_database']
      }
    },
    {
      name: 'sorts',
      label: 'Sorts (JSON)',
      type: 'textarea',
      rows: 3,
      placeholder: `[
  {
    "property": "Created",
    "direction": "descending"
  }
]`,
      conditional: {
        field: 'operation',
        values: ['query_database']
      }
    },
    {
      name: 'parentConfig',
      label: 'Parent Config (JSON)',
      type: 'textarea',
      rows: 3,
      placeholder: `{
  "database_id": "your-database-id"
}`,
      conditional: {
        field: 'operation',
        values: ['create_page']
      }
    },
    {
      name: 'pageProperties',
      label: 'Page Properties (JSON)',
      type: 'textarea',
      rows: 4,
      placeholder: `{
  "Name": {
    "title": [
      {
        "type": "text",
        "text": {"content": "{{title}}"}
      }
    ]
  },
  "Status": {
    "select": {
      "name": "In Progress"
    }
  }
}`,
      conditional: {
        field: 'operation',
        values: ['create_page']
      }
    },
    {
      name: 'children',
      label: 'Children Blocks (JSON)',
      type: 'textarea',
      rows: 5,
      placeholder: `[
  {
    "object": "block",
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {
          "type": "text",
          "text": {"content": "Page content: {{content}}"}
        }
      ]
    }
  }
]`,
      conditional: {
        field: 'operation',
        values: ['create_page']
      }
    }
  ]
};

export default notionConfig;