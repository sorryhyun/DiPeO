// Generated field configuration for start
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const startFields: UnifiedFieldDefinition[] = [
  {
    name: 'trigger_mode',
    type: 'select',
    label: 'Trigger mode',
    required: true,
    defaultValue: "none",
    description: 'How this start node is triggered',
    options: [
      { value: 'none', label: 'None - Simple start point' },
      { value: 'manual', label: 'Manual - Triggered manually with data' },
      { value: 'hook', label: 'Hook - Triggered by external events' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'custom_data',
    type: 'text',
    label: 'Custom data',
    required: false,
    description: 'Custom data to pass when manually triggered',
  },
  {
    name: 'output_data_structure',
    type: 'code',
    label: 'Output data structure',
    required: false,
    description: 'Expected output data structure',
  },
  {
    name: 'hook_event',
    type: 'text',
    label: 'Hook event',
    required: false,
    placeholder: 'e.g., webhook.received, file.uploaded',
    description: 'Event name to listen for',
  },
  {
    name: 'hook_filters',
    type: 'code',
    label: 'Hook filters',
    required: false,
    description: 'Filters to apply to incoming events',
  },
];