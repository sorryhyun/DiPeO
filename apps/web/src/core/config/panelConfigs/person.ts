import type { PanelLayoutConfig, PersonFormData } from '@/features/diagram-editor/types/panel';
import { apolloClient } from '@/graphql/client';
import { GetApiKeysDocument, GetAvailableModelsDocument } from '@/__generated__/graphql';

interface ExtendedPersonFormData extends PersonFormData {
  apiKeyId?: string;
  model?: string;
  label?: string;
  systemPrompt?: string;
}

export const personPanelConfig: PanelLayoutConfig<ExtendedPersonFormData> = {
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
          const { data } = await apolloClient.query({
            query: GetApiKeysDocument,
            fetchPolicy: 'network-only'
          });
          return data.apiKeys.map((key: any) => ({
            value: key.id,
            label: `${key.label} (${key.service})`
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
      name: 'model',
      label: 'Model',
      options: async (formData: unknown) => {
        const data = formData as Record<string, unknown>;
        if (!data.apiKeyId) {
          return [];
        }
        try {
          // Get service from selected API key
          const { data: apiKeysData } = await apolloClient.query({
            query: GetApiKeysDocument,
            fetchPolicy: 'cache-first'
          });
          const selectedKey = apiKeysData.apiKeys.find((k: any) => k.id === data.apiKeyId);
          if (!selectedKey) {
            return [];
          }
          
          const { data: modelsData } = await apolloClient.query({
            query: GetAvailableModelsDocument,
            variables: {
              service: selectedKey.service,
              apiKeyId: data.apiKeyId as string
            }
          });
          
          if (!modelsData || !modelsData.availableModels) {
            console.warn('No models data received from API');
            return [];
          }
          
          return modelsData.availableModels.map((model: string) => ({
            value: model,
            label: model
          }));
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