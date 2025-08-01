// Generated field configuration for condition
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const conditionFields: UnifiedFieldDefinition[] = [
  {
    name: 'condition_type',
    type: 'text',
    label: 'Condition Type',
    required: true,
    description: 'Type of condition to evaluate',
  },
  {
    name: 'expression',
    type: 'text',
    label: 'Expression',
    required: false,
    description: 'Boolean expression to evaluate',
  },
  {
    name: 'node_indices',
    type: 'text',
    label: 'Node Indices',
    required: false,
    description: 'Node indices for condition evaluation',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];