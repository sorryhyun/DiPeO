import type { UnifiedFieldDefinition } from '../field-registry';
import type { JobNodeData } from '@/core/types';

export const jobFields: UnifiedFieldDefinition<JobNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter job label'
  },
  {
    name: 'sub_type',
    type: 'select',
    label: 'Job Type',
    required: true,
    options: [
      { value: 'shell', label: 'Shell Command' },
      { value: 'python', label: 'Python Script' }
    ]
  },
  {
    name: 'command',
    type: 'variableTextArea',
    label: 'Command/Script',
    required: true,
    placeholder: 'Enter command or script',
    rows: 5
  }
];