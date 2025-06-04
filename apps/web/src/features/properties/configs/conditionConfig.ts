import { PanelConfig } from '@/common/types/panelConfig';
import { ConditionBlockData } from '@/common/types';

export const conditionConfig: PanelConfig<ConditionBlockData> = {
  layout: 'single',
  fields: [
    {
      type: 'row',
      className: 'grid grid-cols-2 gap-2',
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
        }
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