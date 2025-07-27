// Generated field configuration for start
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const startFields: UnifiedFieldDefinition[] = [
  {
    name: 'custom_data',
    type: 'text',
    label: 'Custom Data',
    required: true,
    description: 'Custom Data configuration',
  },
  {
    name: 'hook_event',
    type: 'text',
    label: 'Hook Event',
    required: false,
    description: 'Hook Event configuration',
  },
  {
    name: 'hook_filters',
    type: 'code',
    label: 'Hook Filters',
    required: false,
    description: 'Hook Filters configuration',
  },
  {
    name: 'output_data_structure',
    type: 'code',
    label: 'Output Data Structure',
    required: true,
    description: 'Output Data Structure configuration',
  },
  {
    name: 'trigger_mode',
    type: 'select',
    label: 'Trigger Mode',
    required: false,
    description: 'Trigger Mode configuration',
    options: [
      { value: 'manual', label: 'Manual' },
      { value: 'hook', label: 'Hook' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];