import type { UnifiedFieldDefinition } from '../field-registry';
import type { HookNodeData } from '@/core/types';

export const hookFields: UnifiedFieldDefinition<HookNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter hook label'
  },
  {
    name: 'event',
    type: 'select',
    label: 'Event Type',
    required: true,
    options: [
      { value: 'on_start', label: 'On Start' },
      { value: 'on_complete', label: 'On Complete' },
      { value: 'on_error', label: 'On Error' },
      { value: 'custom', label: 'Custom Event' }
    ]
  },
  {
    name: 'custom_event',
    type: 'text',
    label: 'Custom Event Name',
    placeholder: 'Enter custom event name',
    conditional: {
      field: 'event',
      values: ['custom']
    }
  },
  {
    name: 'action',
    type: 'variableTextArea',
    label: 'Action',
    required: true,
    placeholder: 'Define the hook action',
    rows: 5
  }
];