import type { NodeConfigItem } from '../types';

export const conditionNodeConfig: NodeConfigItem = {
  label: 'Condition',
  icon: '🔀',
  color: 'purple',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [
      { id: 'true', position: 'right', label: 'True', offset: { x: 0, y: -40 }, color: '#16a34a' },
      { id: 'false', position: 'right', label: 'False', offset: { x: 0, y: 40 }, color: '#dc2626' }
    ]
  },
  fields: [
    { 
      name: 'conditionType', 
      type: 'select', 
      label: 'Condition Type', 
      required: true,
      options: [
        { value: 'simple', label: 'Simple Condition' },
        { value: 'complex', label: 'Complex Condition' },
        { value: 'detect_max_iterations', label: 'Detect Max Iterations' }
      ]
    },
    { name: 'condition', type: 'string', label: 'Condition', required: true, placeholder: 'e.g., {{value}} > 10' }
  ],
  defaults: { conditionType: 'simple', condition: '' }
};