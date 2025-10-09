// Generated field configuration for sub_diagram
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const subDiagramFields: UnifiedFieldDefinition[] = [
  {
    name: 'diagram_name',
    type: 'text',
    label: '"Diagram name"',
    required: false,
    placeholder: '"Select diagram..."',
    description: '"Name of the diagram to execute (e.g., \'workflow/process\')"',
  },
  {
    name: 'diagram_data',
    type: 'textarea',
    label: '"Diagram data"',
    required: false,
    description: '"Inline diagram data (alternative to diagram_name)"',
  },
  {
    name: 'input_mapping',
    type: 'textarea',
    label: '"Input mapping"',
    required: false,
    description: '"Map node inputs to sub-diagram variables"',
  },
  {
    name: 'output_mapping',
    type: 'textarea',
    label: '"Output mapping"',
    required: false,
    description: '"Map sub-diagram outputs to node outputs"',
  },
  {
    name: 'timeout',
    type: 'text',
    label: '"Timeout"',
    required: false,
    description: '"Execution timeout in seconds"',
    min: 1,
    max: 3600,
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
    label: '"Wait for completion"',
    required: false,
    description: '"Whether to wait for sub-diagram completion"',
  },
  {
    name: 'isolate_conversation',
    type: 'checkbox',
    label: '"Isolate conversation"',
    required: false,
    description: '"Create isolated conversation context for sub-diagram"',
  },
  {
    name: 'ignore_if_sub',
    type: 'checkbox',
    label: '"Ignore if sub"',
    required: false,
    description: '"Skip execution if this diagram is being run as a sub-diagram"',
  },
  {
    name: 'diagram_format',
    type: 'text',
    label: '"Diagram format"',
    required: false,
    description: '"Format of the diagram file (yaml, json, or light)"',
    options: [
      { value: '"yaml"', label: '"YAML"' },
      { value: '"json"', label: '"JSON"' },
      { value: '"light"', label: '"Light"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'batch',
    type: 'checkbox',
    label: '"Batch"',
    required: false,
    description: '"Execute sub-diagram in batch mode for multiple inputs"',
  },
  {
    name: 'batch_input_key',
    type: 'password',
    label: '"Batch input key"',
    required: false,
    placeholder: '"items"',
    description: '"Key in inputs containing the array of items for batch processing"',
  },
  {
    name: 'batch_parallel',
    type: 'checkbox',
    label: '"Batch parallel"',
    required: false,
    description: '"Execute batch items in parallel"',
  },
];
