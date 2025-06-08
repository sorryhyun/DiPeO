import type { TypedPanelConfig, ConditionFormData } from '@/types/ui';

export const conditionPanelConfig: TypedPanelConfig<ConditionFormData> = {
  layout: 'single',
  fields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Condition'
    },
    {
      type: 'select',
      name: 'conditionType',
      label: 'Condition Type',
      options: [
        { value: 'expression', label: 'Expression' },
        { value: 'detect_max_iterations', label: 'Max Iterations' }
      ]
    },
    {
      type: 'textarea',
      name: 'expression',
      label: 'Python Expression',
      rows: 3,
      placeholder: 'e.g., x > 10 and y == \'yes\'',
      conditional: {
        field: 'conditionType',
        values: ['expression'],
        operator: 'equals'
      },
      validate: (value, formData) => {
        if (formData.conditionType === 'expression' && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'Expression is required when type is Expression' };
        }
        return { isValid: true };
      }
    }
  ]
};