import type { EndpointFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const endpointConfig = createUnifiedConfig<EndpointFormData>({
  // Node configuration
  label: 'Endpoint',
  icon: '🎯',
  color: 'red',
  handles: {
    input: [{ id: 'default', position: 'left' }]
  },
  fields: [], // Fields are defined in panelCustomFields to match backend expectations
  defaults: { label: '', save_to_file: false, file_path: '', file_format: 'text' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'save_to_file', 'file_path', 'file_format'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'End',
      column: 1
    },
    {
      type: 'checkbox',
      name: 'save_to_file',
      label: 'Save to File',
      column: 1
    },
    {
      type: 'text',
      name: 'file_path',
      label: 'File Path',
      placeholder: 'files/output.txt',
      column: 2,
      conditional: {
        field: 'save_to_file',
        values: [true],
        operator: 'equals'
      },
      validate: (value, formData) => {
        if (formData?.save_to_file && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'File path is required when saving to file' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'select',
      name: 'file_format',
      label: 'Format',
      column: 2,
      options: [
        { value: 'text', label: 'Text' },
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' }
      ],
      conditional: {
        field: 'save_to_file',
        values: [true],
        operator: 'equals'
      }
    }
  ]
});