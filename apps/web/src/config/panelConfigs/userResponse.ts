import type { TypedPanelConfig, UserResponseFormData } from '@/types/ui';

export const userResponsePanelConfig: TypedPanelConfig<UserResponseFormData> = {
  layout: 'single',
  fields: [
    {
      type: 'text',
      name: 'label',
      label: 'Name',
      placeholder: 'User Response'
    },
    {
      type: 'textarea',
      name: 'prompt',
      label: 'Prompt Message',
      placeholder: 'Enter the message to show to the user...',
      rows: 3,
      required: true,
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Prompt message is required' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'text',
      name: 'timeout',
      label: 'Timeout (seconds)',
      placeholder: '10',
      validate: (value) => {
        if (value && (isNaN(Number(value)) || Number(value) < 1 || Number(value) > 60)) {
          return { isValid: false, error: 'Timeout must be between 1 and 60 seconds' };
        }
        return { isValid: true };
      }
    }
  ]
};