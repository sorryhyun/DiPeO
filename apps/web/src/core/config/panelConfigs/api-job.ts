import type { UnifiedFieldDefinition } from '../field-registry';
import type { ApiJobNodeData } from '@/core/types';

export const apiJobFields: UnifiedFieldDefinition<ApiJobNodeData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Label',
    required: true,
    placeholder: 'Enter API job label'
  },
  {
    name: 'url',
    type: 'text',
    label: 'URL',
    required: true,
    placeholder: 'https://api.example.com/endpoint'
  },
  {
    name: 'method',
    type: 'select',
    label: 'Method',
    required: true,
    options: [
      { value: 'GET', label: 'GET' },
      { value: 'POST', label: 'POST' },
      { value: 'PUT', label: 'PUT' },
      { value: 'DELETE', label: 'DELETE' },
      { value: 'PATCH', label: 'PATCH' }
    ],
    defaultValue: 'GET'
  },
  {
    name: 'headers',
    type: 'variableTextArea',
    label: 'Headers (JSON)',
    placeholder: '{"Content-Type": "application/json"}',
    rows: 3
  },
  {
    name: 'body',
    type: 'variableTextArea',
    label: 'Body',
    placeholder: 'Request body (for POST, PUT, PATCH)',
    rows: 5,
    conditional: {
      field: 'method',
      values: ['POST', 'PUT', 'PATCH'],
      operator: 'includes'
    }
  }
];