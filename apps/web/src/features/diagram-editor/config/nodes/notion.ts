import { HandleLabel } from '@dipeo/domain-models';
import type { NotionNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Notion node type
 * Combines visual metadata, node structure, and field definitions
 */
export const NotionNodeConfig: UnifiedNodeConfig<NotionNodeData> = {
  // Visual metadata
  label: 'Notion',
  icon: '📝',
  color: '#ec4899',
  nodeType: 'notion' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Notion', 
    page_id: '', 
    operation: 'read' 
  },
  
  // Panel layout configuration
  panelLayout: 'single',
  panelFieldOrder: ['label', 'api_key', 'database_id', 'operation'],
  
  // Field definitions
  customFields: [
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
  ]
};