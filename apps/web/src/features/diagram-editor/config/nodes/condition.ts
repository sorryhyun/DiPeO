import { HandleLabel, NodeType } from '@dipeo/domain-models';
import type { ConditionNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Condition node type
 * Combines visual metadata, node structure, and field definitions
 */
export const ConditionNodeConfig: UnifiedNodeConfig<ConditionNodeData> = {
  // Visual metadata
  label: 'Condition',
  icon: '🔀',
  color: '#f59e0b',
  nodeType: 'condition' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [
      { id: HandleLabel.CONDITION_TRUE, position: 'right', label: 'true', offset: { x: 0, y: 30 } },
      { id: HandleLabel.CONDITION_FALSE, position: 'right', label: 'false', offset: { x: 0, y: -30 } }
    ]
  },
  
  // Default values
  defaults: { 
    label: 'Condition', 
    condition_type: 'custom', 
    expression: '' 
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'condition_type', 'expression'],
  
  // Field definitions
  customFields: [
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
      defaultValue: 'custom',
      column: 1
    },
    {
      name: 'expression',
      type: 'variableTextArea',
      label: 'Condition Expression',
      required: true,
      placeholder: 'Enter condition expression. Use {{variable_name}} for variables.',
      rows: 3,
      column: 2,
      conditional: {
        field: 'condition_type',
        values: ['custom'],
        operator: 'equals'
      },
      validate: (value: unknown, formData: ConditionNodeData) => {
        if (formData?.condition_type === 'custom' && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'Expression is required for custom conditions' };
        }
        return { isValid: true };
      }
    }
  ]
};