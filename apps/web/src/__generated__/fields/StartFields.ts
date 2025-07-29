// Generated field configuration for start
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const startFields: UnifiedFieldDefinition[] = [
  {
    name: 'custom_data',
    type: 'text',
    label: 'Custom Data',
    required: false,
    description: 'Custom data to pass when manually triggered',
  },
  {
    name: 'hook_event',
    type: 'text',
    label: 'Hook Event',
    required: false,
    placeholder: 'e.g., webhook.received, file.uploaded',
    description: 'Event name to listen for',
  },
  {
    name: 'hook_filters',
    type: 'code',
    label: 'Hook Filters',
    required: false,
    description: 'Filters to apply to incoming events',
  },
  {
    name: 'output_data_structure',
    type: 'code',
    label: 'Output Data Structure',
    required: false,
    description: 'Expected output data structure',
  },
  {
    name: 'trigger_mode',
    type: 'select',
    label: 'Trigger Mode',
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
];