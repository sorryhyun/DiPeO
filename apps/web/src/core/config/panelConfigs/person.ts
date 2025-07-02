import type { PanelLayoutConfig, PersonFormData } from '@/features/diagram-editor/types/panel';
import { apolloClient } from '@/graphql/client';
import { GetApiKeysDocument, GetAvailableModelsDocument, type GetApiKeysQuery } from '@/__generated__/graphql';

interface ExtendedPersonFormData extends PersonFormData {
  apiKeyId?: string;
  model?: string;
  label?: string;
  systemPrompt?: string;
  temperature?: number;
  'llmConfig.apiKeyId'?: string;
  'llmConfig.model'?: string;
  'llmConfig.systemPrompt'?: string;
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
      name: 'llmConfig.apiKeyId',
      label: 'API Key',
      options: async () => {
        try {
          const { data } = await apolloClient.query<GetApiKeysQuery>({
            query: GetApiKeysDocument,
            fetchPolicy: 'network-only'
          });
          return data.api_keys.map((key) => ({
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
      name: 'llmConfig.model',
      label: 'Model',
      options: async (formData: unknown) => {
        const data = formData as Record<string, unknown>;
        const apiKeyId = data['llmConfig.apiKeyId'] as string;
        if (!apiKeyId) {
          return [];
        }
        try {
          // Get service from selected API key
          const { data: apiKeysData } = await apolloClient.query<GetApiKeysQuery>({
            query: GetApiKeysDocument,
            fetchPolicy: 'cache-first'
          });
          const selectedKey = apiKeysData.api_keys.find((k) => k.id === apiKeyId);
          if (!selectedKey) {
            return [];
          }
          
          const { data: modelsData } = await apolloClient.query({
            query: GetAvailableModelsDocument,
            variables: {
              service: selectedKey.service,
              apiKeyId
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
      dependsOn: ['llmConfig.apiKeyId'],
      placeholder: 'Select Model'
    },
    {
      type: 'number',
      name: 'temperature',
      label: 'Temperature',
      placeholder: '0.7',
      min: 0,
      max: 2
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'llmConfig.systemPrompt',
      label: 'System Prompt',
      placeholder: 'Enter system prompt',
      rows: 4
    }
  ]
};