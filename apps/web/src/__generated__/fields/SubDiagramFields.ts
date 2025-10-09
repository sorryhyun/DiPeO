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
    name: 'batch_input_key',
    type: 'password',
    label: '"Batch input key"',
    required: false,
    placeholder: '"items"',
    description: '"Key in inputs containing the array of items for batch processing"',
  },
];
