import type { PanelConfig } from '@/types';

export const userResponsePanelConfig: PanelConfig<Record<string, any>> = {
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
      rows: 3
    },
    {
      type: 'text',
      name: 'timeout',
      label: 'Timeout (seconds)',
      placeholder: '10'
    }
  ]
};