import { PanelConfig } from '@/shared/types/panelConfig';
import { ConditionBlockData } from '@/shared/types';

export const conditionConfig: PanelConfig<ConditionBlockData> = {
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
        { value: 'expression', label: 'Python Expression' },
        { value: 'max_iterations', label: 'Detect Max Iterations' }
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
      }
    }
  ]
};