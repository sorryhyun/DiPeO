import type { UnifiedFieldDefinition } from '../field-registry';
import type { DBNodeData } from '@/core/types';

export const dbFields: UnifiedFieldDefinition<DBNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter database label'
  },
  {
    name: 'sub_type',
    type: 'select',
    label: 'Source Type',
    required: true,
    options: [
      { value: 'fixed_prompt', label: 'Fixed Prompt' },
      { value: 'file', label: 'File' }
    ]
  },
  {
    name: 'operation',
    type: 'select',
    label: 'Operation',
    required: true,
    options: [
      { value: 'prompt', label: 'Prompt' },
      { value: 'read', label: 'Read' },
      { value: 'write', label: 'Write' },
      { value: 'update', label: 'Update' },
      { value: 'delete', label: 'Delete' }
    ]
  },
  {
    name: 'source_details',
    type: 'variableTextArea',
    label: 'Source Details',
    placeholder: 'Enter content or file path...',
    rows: 6,
    showPromptFileButton: true
  }
];