// Generated field configuration for start
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const startFields: UnifiedFieldDefinition[] = [
  {
    name: 'trigger_mode',
    type: 'text',
    label: '"Trigger mode"',
    required: false,
    description: '"How this start node is triggered"',
    options: [
      { value: '"HookTriggerMode.NONE"', label: '"None - Simple start point"' },
      { value: '"HookTriggerMode.MANUAL"', label: '"Manual - Triggered manually with data"' },
      { value: '"HookTriggerMode.HOOK"', label: '"Hook - Triggered by external events"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'custom_data',
    type: 'text',
    label: '"Custom data"',
    required: false,
    description: '"Custom data to pass when manually triggered"',
  },
  {
    name: 'output_data_structure',
    type: 'textarea',
    label: '"Output data structure"',
    required: false,
    description: '"Expected output data structure"',
  },
  {
    name: 'hook_event',
    type: 'text',
    label: '"Hook event"',
    required: false,
    placeholder: '"e.g., webhook.received, file.uploaded"',
    description: '"Event name to listen for"',
  },
  {
    name: 'hook_filters',
    type: 'textarea',
    label: '"Hook filters"',
    required: false,
    description: '"Filters to apply to incoming events"',
  },
];
