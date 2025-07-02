import type { ConditionFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const conditionConfig = createUnifiedConfig<ConditionFormData>({
  // Node configuration
  label: 'Condition',
  icon: '🔀',
  color: 'purple',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [
      { id: 'true', position: 'right', label: 'True', offset: { x: 0, y: 40 }, color: '#16a34a' },
      { id: 'false', position: 'right', label: 'False', offset: { x: 0, y: -40 }, color: '#dc2626' }
    ]
  },
  fields: [
    { 
      name: 'condition_type', 
      type: 'select', 
      label: 'Type', 
      required: true,
      options: [
        { value: 'simple', label: 'Simple Condition' },
        { value: 'complex', label: 'Complex Condition' },
        { value: 'detect_max_iterations', label: 'Detect Max Iterations' }
      ]
    },
    { 
      name: 'condition', 
      type: 'string', 
      label: 'Condition', 
      required: true, 
      placeholder: 'e.g., {{value}} > 10'
    }
  ],
  defaults: { condition_type: 'simple', condition: '', label: '' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'condition_type', 'condition', 'expression'],
  panelFieldOverrides: {
    condition_type: {
      options: [
        { value: 'expression', label: 'Expression' },
        { value: 'detect_max_iterations', label: '🔁 Max Iterations' }
      ],
      column: 2
    },
    condition: {
      column: 2,
      disabled: (formData) => formData?.condition_type === 'detect_max_iterations'
    }
  },
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Condition',
      column: 1,
      validate: (_value) => ({
        isValid: true // Label is optional
      })
    },
    {
      type: 'variableTextArea',
      name: 'expression',
      label: 'Expression',
      placeholder: "e.g., x > 10 and y == 'yes' (Python syntax)",
      rows: 3,
      column: 2,
      conditional: {
        field: 'condition_type',
        values: ['expression'],
        operator: 'equals'
      },
      validate: (value, formData) => {
        if (formData?.condition_type === 'expression' && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'Expression is required' };
        }
        return { isValid: true };
      }
    }
  ]
});