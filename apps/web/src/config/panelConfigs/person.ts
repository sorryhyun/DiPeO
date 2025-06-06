import type { PanelConfig } from '@/types';
import { fetchApiKeys, fetchAvailableModels } from '@/utils/api';

export const personPanelConfig: PanelConfig<Record<string, unknown>> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Person Name',
      placeholder: 'Person Name'
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
      ]
    },
    {
      type: 'select',
      name: 'apiKeyId',
      label: 'API Key',
      options: async () => {
        try {
          const apiKeys = await fetchApiKeys();
          return apiKeys.map(key => ({
            value: key.id,
            label: `${key.name} (${key.service})`
          }));
        } catch (error) {
          console.error('Failed to fetch API keys:', error);
          return [];
        }
      },
      placeholder: 'Select API Key'
    },
    {
      type: 'select',
      name: 'modelName',
      label: 'Model',
      options: async (formData: unknown) => {
        const data = formData as Record<string, unknown>;
        if (!data.service || !data.apiKeyId) {
          return [];
        }
        try {
          return await fetchAvailableModels(data.service as string, data.apiKeyId as string);
        } catch (error) {
          console.error('Failed to fetch models:', error);
          return [];
        }
      },
      dependsOn: ['service', 'apiKeyId'],
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