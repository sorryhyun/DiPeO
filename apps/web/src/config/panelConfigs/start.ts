import type { TypedPanelConfig, StartFormData } from '@/types/ui';

export const startPanelConfig: TypedPanelConfig<StartFormData> = {
  layout: 'single',
  fields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Start',
      validate: (_value) => ({
        isValid: true // Label is optional
      })
    }
  ]
};