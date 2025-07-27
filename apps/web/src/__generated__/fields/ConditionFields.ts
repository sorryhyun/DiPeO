// Generated field configuration for condition
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const conditionFields: UnifiedFieldDefinition[] = [
  {
    name: 'condition_type',
    type: 'text',
    label: 'Condition Type',
    required: true,
    description: 'Condition Type configuration',
  },
  {
    name: 'expression',
    type: 'text',
    label: 'Expression',
    required: false,
    description: 'Expression configuration',
  },
  {
    name: 'node_indices',
    type: 'text',
    label: 'Node Indices',
    required: false,
    description: 'Node Indices configuration',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];