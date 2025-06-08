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
        if (!data.apiKeyId) {
          return [];
        }
        try {
          // Get service from selected API key
          const apiKeys = await fetchApiKeys();
          const selectedKey = apiKeys.find(k => k.id === data.apiKeyId);
          if (!selectedKey) {
            return [];
          }
          return await fetchAvailableModels(selectedKey.service, data.apiKeyId as string);
        } catch (error) {
          console.error('Failed to fetch models:', error);
          return [];
        }
      },
      dependsOn: ['apiKeyId'],
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