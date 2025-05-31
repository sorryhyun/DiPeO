import { PanelConfig } from '@/shared/types/panelConfig';
import { PersonDefinition } from '@/shared/types';

export const personConfig: PanelConfig<PersonDefinition> = {
  layout: 'single',
  fields: [
    {
      type: 'row',
      fields: [
        {
          type: 'text',
          name: 'label',
          label: 'Person Name',
          placeholder: 'Person Name',
          className: 'flex-1'
        },
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
        }
      ]
    },
    {
      type: 'row',
      fields: [
        {
          type: 'select',
          name: 'apiKeyId',
          label: 'API Key',
          options: [],  // Will be populated dynamically
          placeholder: 'Select API Key',
          className: 'flex-1'
        },
        {
          type: 'select',
          name: 'modelName',
          label: 'Model',
          options: [],  // Will be populated dynamically
          placeholder: 'Select Model',
          className: 'flex-1'
        }
      ]
    },
    {
      type: 'textarea',
      name: 'systemPrompt',
      label: 'System Prompt',
      placeholder: 'Enter system prompt',
      rows: 4
    }
  ]
};