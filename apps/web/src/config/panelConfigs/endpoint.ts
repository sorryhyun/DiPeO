import type { TypedPanelConfig, EndpointFormData } from '@/types/ui';

export const endpointPanelConfig: TypedPanelConfig<EndpointFormData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'End'
    },
    {
      type: 'checkbox',
      name: 'saveToFile',
      label: 'Save output to file'
    },
    {
      type: 'text',
      name: 'filePath',
      label: 'File Path',
      placeholder: 'results/output.txt',
      conditional: {
        field: 'saveToFile',
        values: [true]
      },
      validate: (value, formData) => {
        if (formData.saveToFile && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'File path is required when saving to file' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'select',
      name: 'fileFormat',
      label: 'File Format',
      options: [
        { value: 'text', label: 'Plain Text' },
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' }
      ],
      conditional: {
        field: 'saveToFile',
        values: [true]
      }
    }
  ],
  rightColumn: []
};