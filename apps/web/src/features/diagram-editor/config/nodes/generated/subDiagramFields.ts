// Generated field configuration for sub_diagram
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const subDiagramFields: UnifiedFieldDefinition[] = [
  {
    name: 'diagram_name',
    type: 'text',
    label: 'Diagram Name',
    required: false,
    description: 'Name of the diagram to execute (e.g., &#x27;workflow/process&#x27;)',
  },
  {
    name: 'diagram_data',
    type: 'text',
    label: 'Diagram Data',
    required: false,
    description: 'Inline diagram data (alternative to diagram_name)',
  },
  {
    name: 'input_mapping',
    type: 'text',
    label: 'Input Mapping',
    required: false,
    description: 'Map node inputs to sub-diagram variables',
  },
  {
    name: 'output_mapping',
    type: 'text',
    label: 'Output Mapping',
    required: false,
    description: 'Map sub-diagram outputs to node outputs',
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    description: 'Execution timeout in seconds',
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      if (typeof value === 'number' && value > 3600) {
        return { isValid: false, error: 'Value must be at most 3600' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'wait_for_completion',
    type: 'checkbox',
    label: 'Wait For Completion',
    required: false,
    defaultValue: true,
    description: 'Whether to wait for sub-diagram completion',
  },
  {
    name: 'isolate_conversation',
    type: 'checkbox',
    label: 'Isolate Conversation',
    required: false,
    description: 'Create isolated conversation context for sub-diagram',
  },
];