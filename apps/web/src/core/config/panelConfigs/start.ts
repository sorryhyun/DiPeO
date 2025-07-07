import type { UnifiedFieldDefinition } from '../field-registry';
import type { StartNodeData } from '@/core/types';

export const startFields: UnifiedFieldDefinition<StartNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter start node label'
  },
  {
    name: 'enable_hook',
    type: 'checkbox',
    label: 'Enable Hook',
    defaultValue: false
  },
  {
    name: 'hook_type',
    type: 'select',
    label: 'Hook Type',
    options: [
      { value: 'webhook', label: 'Webhook' },
      { value: 'file', label: 'File' },
      { value: 'shell', label: 'Shell' }
    ],
    conditional: {
      field: 'enable_hook',
      values: [true]
    }
  },
  {
    name: 'hook_config',
    type: 'textarea',
    label: 'Hook Configuration',
    placeholder: 'Hook configuration (e.g., URL, file path, or command)',
    rows: 4,
    conditional: {
      field: 'enable_hook',
      values: [true]
    }
  }
];