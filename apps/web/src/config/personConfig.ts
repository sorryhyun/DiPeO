import { PanelConfig } from '@/types';
import { getApiKeyOptions, getDynamicModelOptions } from '../utils/propertyHelpers';

export const personConfig: PanelConfig<Record<string, any>> = {
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
          options: getApiKeyOptions,  // Function to get current API keys
          placeholder: 'Select API Key',
          className: 'flex-1'
        }
      ]
    },
    {
      type: 'select',
      name: 'modelName',
      label: 'Model',
      options: (formData: unknown) => {
        const data = formData as Record<string, any>;
        return getDynamicModelOptions(data.service, data.apiKeyId);
      },
      placeholder: 'Select Model',
      dependsOn: ['service', 'apiKeyId']  // Reload when service or API key changes
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