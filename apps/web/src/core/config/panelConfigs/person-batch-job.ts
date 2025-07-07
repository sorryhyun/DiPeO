import type { UnifiedFieldDefinition } from '../field-registry';
import type { PersonBatchJobNodeData } from '@/core/types';

export const personBatchJobFields: UnifiedFieldDefinition<PersonBatchJobNodeData>[] = [
  {
    name: 'labelPersonRow',
    type: 'labelPersonRow',
    label: '',
    required: true,
    labelPlaceholder: 'Enter batch job label',
    personPlaceholder: 'Select a person'
  },
  {
    name: 'batch_key',
    type: 'text',
    label: 'Batch Key',
    required: true,
    placeholder: 'Key containing the array to iterate over'
  },
  {
    name: 'prompt',
    type: 'variableTextArea',
    label: 'Prompt Template',
    required: true,
    placeholder: 'Use {{item}} for current batch item, {{variable_name}} for other variables',
    rows: 5,
    showPromptFileButton: true
  }
];