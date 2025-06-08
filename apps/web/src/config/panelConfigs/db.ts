import type { TypedPanelConfig, DBFormData } from '@/types/ui';

export const dbPanelConfig: TypedPanelConfig<DBFormData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Label',
      placeholder: 'Database'
    },
    {
      type: 'select',
      name: 'subType',
      label: 'Source Type',
      options: [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ]
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'sourceDetails',
      label: 'Source Details',
      rows: 5,
      placeholder: 'For Fixed Prompt: Enter your text content\nFor File: Enter the file path (e.g., data/input.txt)',
      required: true,
      validate: (value, formData) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Source details are required' };
        }
        if (formData.subType === 'file' && !value.includes('/') && !value.includes('.')) {
          return { isValid: false, error: 'Please provide a valid file path' };
        }
        return { isValid: true };
      }
    }
  ]
};