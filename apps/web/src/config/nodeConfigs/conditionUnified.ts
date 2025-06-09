import type { ConditionFormData } from '@/types/ui';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for Condition node
 * This replaces both the node config and panel config
 */
export const conditionUnifiedConfig = createUnifiedConfig<ConditionFormData>({
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
      name: 'conditionType', 
      type: 'select', 
      label: 'Type', 
      required: true,
      options: [
        { value: 'simple', label: 'Simple Condition' },
        { value: 'complex', label: 'Complex Condition' },
        { value: 'detect_max_iterations', label: 'Detect Max Iterations' }
      ]
    },
    { name: 'condition', type: 'string', label: 'Condition', required: true, placeholder: 'e.g., {{value}} > 10' }
  ],
  defaults: { conditionType: 'simple', condition: '', label: '' },
  
  // Panel configuration overrides
  panelLayout: 'single',
  panelFieldOrder: ['label', 'conditionType', 'expression'],
  panelFieldOverrides: {
    conditionType: {
      options: [
        { value: 'expression', label: 'Expression' },
        { value: 'detect_max_iterations', label: 'Max Iterations' }
      ]
    }
  },
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Condition',
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
      conditional: {
        field: 'conditionType',
        values: ['expression'],
        operator: 'equals'
      },
      validate: (value, formData) => {
        if (formData?.conditionType === 'expression' && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'Expression is required' };
        }
        return { isValid: true };
      }
    }
  ]
});