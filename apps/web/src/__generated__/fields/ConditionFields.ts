// Generated field configuration for condition
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const conditionFields: UnifiedFieldDefinition[] = [
  {
    name: 'condition_type',
    type: 'select',
    label: 'Condition type',
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
    label: 'Node indices',
    required: false,
    placeholder: 'Select nodes to monitor',
    description: 'Node indices for detect_max_iteration condition',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'expose_index_as',
    type: 'text',
    label: 'Expose index as',
    required: false,
    placeholder: 'e.g., current_index, loop_counter',
    description: 'Variable name to expose the condition node\'s execution count (0-based index) to downstream nodes',
  },
];