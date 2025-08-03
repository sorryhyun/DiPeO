







// Generated field configuration for condition
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const conditionFields: UnifiedFieldDefinition[] = [
  {
    name: 'condition_type',
    type: 'select',
    label: 'Condition Type',
    required: false,
    defaultValue: "custom",
    description: 'Type of condition to evaluate',
    options: [
      { value: 'detect_max_iterations', label: 'Detect Max Iterations' },
      { value: 'check_nodes_executed', label: 'Check Nodes Executed' },
      { value: 'custom', label: 'Custom Expression' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'expression',
    type: 'textarea',
    label: 'Expression',
    required: false,
    placeholder: 'e.g., inputs.value > 10',
    description: 'Boolean expression to evaluate',
    rows: 3,
  },
  {
    name: 'node_indices',
    type: 'nodeSelect',
    label: 'Node Indices',
    required: false,
    placeholder: 'Select nodes to monitor',
    description: 'Node indices for detect_max_iteration condition',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];