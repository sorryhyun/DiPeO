import type { UnifiedFieldDefinition } from '../field-registry';
import type { EndpointNodeData } from '@/core/types';

export const endpointFields: UnifiedFieldDefinition<EndpointNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter endpoint label'
  },
  {
    name: 'output_variable',
    type: 'text',
    label: 'Output Variable',
    placeholder: 'Variable to store the output'
  },
  {
    name: 'save_to_file',
    type: 'checkbox',
    label: 'Save to File',
    defaultValue: false
  },
  {
    name: 'file_format',
    type: 'select',
    label: 'File Format',
    options: [
      { value: 'json', label: 'JSON' },
      { value: 'yaml', label: 'YAML' },
      { value: 'csv', label: 'CSV' },
      { value: 'txt', label: 'Text' }
    ],
    defaultValue: 'json',
    conditional: {
      field: 'save_to_file',
      values: [true]
    }
  },
  {
    name: 'file_name',
    type: 'text',
    label: 'File Name',
    placeholder: 'output.json',
    conditional: {
      field: 'save_to_file',
      values: [true]
    }
  }
];