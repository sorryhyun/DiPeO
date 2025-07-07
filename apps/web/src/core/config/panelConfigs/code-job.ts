import type { UnifiedFieldDefinition } from '../field-registry';
import type { CodeJobNodeData } from '@/core/types';

export const codeJobFields: UnifiedFieldDefinition<CodeJobNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter code job label'
  },
  {
    name: 'language',
    type: 'select',
    label: 'Language',
    required: true,
    options: [
      { value: 'python', label: 'Python' },
      { value: 'javascript', label: 'JavaScript' },
      { value: 'typescript', label: 'TypeScript' }
    ]
  },
  {
    name: 'code',
    type: 'variableTextArea',
    label: 'Code',
    required: true,
    placeholder: 'Enter your code here',
    rows: 10
  }
];