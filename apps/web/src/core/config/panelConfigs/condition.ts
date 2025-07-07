import type { UnifiedFieldDefinition } from '../field-registry';
import type { ConditionNodeData } from '@/core/types';

export const conditionFields: UnifiedFieldDefinition<ConditionNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter condition label'
  },
  {
    name: 'condition_type',
    type: 'select',
    label: 'Condition Type',
    options: [
      { value: 'custom', label: 'Custom Expression' },
      { value: 'equals', label: 'Equals' },
      { value: 'not_equals', label: 'Not Equals' },
      { value: 'contains', label: 'Contains' }
    ],
    defaultValue: 'custom'
  },
  {
    name: 'expression',
    type: 'variableTextArea',
    label: 'Condition Expression',
    required: true,
    placeholder: 'e.g., {{output}} > 0',
    rows: 3,
    conditional: {
      field: 'condition_type',
      values: ['custom']
    },
    validate: (value, formData) => {
      if (formData?.condition_type === 'custom' && (!value || typeof value !== 'string')) {
        return { isValid: false, error: 'Expression is required for custom conditions' };
      }
      return { isValid: true };
    }
  }
];