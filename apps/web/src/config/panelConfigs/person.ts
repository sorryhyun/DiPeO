import type { PanelConfig } from '@/types';

export const personPanelConfig: PanelConfig<Record<string, any>> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Person Name',
      placeholder: 'Person Name'
    },
    {
      type: 'row',
      fields: [
        {
          type: 'select',
          name: 'service',
          label: 'Service',
          options: [
            { value: 'openai', label: 'OpenAI' },
            { value: 'claude', label: 'Claude' },
            { value: 'gemini', label: 'Gemini' },
            { value: 'grok', label: 'Grok' },
            { value: 'custom', label: 'Custom' }
          ],
          className: 'flex-1'
        },
        {
          type: 'select',
          name: 'apiKeyId',
          label: 'API Key',
          options: [], // Dynamic options
          placeholder: 'Select API Key',
          className: 'flex-1'
        }
      ]
    },
    {
      type: 'select',
      name: 'modelName',
      label: 'Model',
      options: [], // Dynamic options based on service
      placeholder: 'Select Model'
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'systemPrompt',
      label: 'System Prompt',
      placeholder: 'Enter system prompt',
      rows: 4
    }
  ]
};