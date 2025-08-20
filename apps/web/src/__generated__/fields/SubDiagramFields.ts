// Generated field configuration for sub_diagram
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const subDiagramFields: UnifiedFieldDefinition[] = [
  {
    name: 'diagram_name',
    type: 'select',
    label: 'Diagram name',
    required: false,
    placeholder: 'Select diagram...',
    description: 'Name of the diagram to execute (e.g., \'workflow/process\')',
  },
  {
    name: 'diagram_data',
    type: 'code',
    label: 'Diagram data',
    required: false,
    description: 'Inline diagram data (alternative to diagram_name)',
  },
  {
    name: 'input_mapping',
    type: 'code',
    label: 'Input mapping',
    required: false,
    placeholder: '{ \"targetVar\": \"sourceInput\" }',
    description: 'Map node inputs to sub-diagram variables',
  },
  {
    name: 'output_mapping',
    type: 'code',
    label: 'Output mapping',
    required: false,
    placeholder: '{ \"outputKey\": \"nodeId.field\" }',
    description: 'Map sub-diagram outputs to node outputs',
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    description: 'Execution timeout in seconds',
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
    label: 'Wait for completion',
    required: false,
    defaultValue: true,
    description: 'Whether to wait for sub-diagram completion',
  },
  {
    name: 'isolate_conversation',
    type: 'checkbox',
    label: 'Isolate conversation',
    required: false,
    defaultValue: false,
    description: 'Create isolated conversation context for sub-diagram',
  },
  {
    name: 'ignoreIfSub',
    type: 'checkbox',
    label: 'Ignoreifsub',
    required: false,
    defaultValue: false,
    description: 'Skip execution if this diagram is being run as a sub-diagram',
  },
  {
    name: 'diagram_format',
    type: 'select',
    label: 'Diagram format',
    required: false,
    description: 'Format of the diagram file (yaml, json, or light)',
    options: [
      { value: 'yaml', label: 'YAML' },
      { value: 'json', label: 'JSON' },
      { value: 'light', label: 'Light' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'batch',
    type: 'checkbox',
    label: 'Batch',
    required: false,
    defaultValue: false,
    description: 'Execute sub-diagram in batch mode for multiple inputs',
  },
  {
    name: 'batch_input_key',
    type: 'text',
    label: 'Batch input key',
    required: false,
    placeholder: 'items',
    description: 'Key in inputs containing the array of items for batch processing',
  },
  {
    name: 'batch_parallel',
    type: 'checkbox',
    label: 'Batch parallel',
    required: false,
    defaultValue: false,
    description: 'Execute batch items in parallel',
  },
];