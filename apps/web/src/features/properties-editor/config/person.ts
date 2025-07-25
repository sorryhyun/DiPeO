import type { PanelLayoutConfig, TypedPanelFieldConfig } from '@/features/diagram-editor/types/panel';
import type { DomainPerson } from '@/core/types';
import { apolloClient } from '@/lib/graphql/client';
import { GetApiKeysDocument, GetAvailableModelsDocument, type GetApiKeysQuery } from '@/__generated__/graphql';
import { isLLMService } from '@dipeo/domain-models';

interface ExtendedPersonData extends Partial<DomainPerson> {
  'llm_config.api_key_id'?: string;
  'llm_config.model'?: string;
  'llm_config.system_prompt'?: string;
  'llm_config.service'?: string;
}

export const personFields: TypedPanelFieldConfig<ExtendedPersonData>[] = [
  {
    name: 'label' as keyof ExtendedPersonData & string,
    type: 'text',
    label: 'Person Name',
    placeholder: 'Person Name',
    column: 1
  },
  {
    name: 'llm_config.api_key_id' as keyof ExtendedPersonData & string,
    type: 'select',
    label: 'API Key',
    column: 1,
    placeholder: 'Select API Key',
    options: async () => {
      try {
        const { data } = await apolloClient.query<GetApiKeysQuery>({
          query: GetApiKeysDocument,
          fetchPolicy: 'network-only'
        });
        // Filter to only show LLM service API keys
        return data.api_keys
          .filter((key) => isLLMService(key.service as any))
          .map((key) => ({
            value: key.id,
            label: `${key.label} (${key.service})`
          }));
      } catch (error) {
        console.error('Failed to fetch API keys:', error);
        return [];
      }
    }
  },
  {
    name: 'llm_config.model' as keyof ExtendedPersonData & string,
    type: 'select',
    label: 'Model',
    column: 1,
    placeholder: 'Select Model',
    dependsOn: ['llm_config.api_key_id'],
    options: async (formData: unknown) => {
      const data = formData as Record<string, unknown>;
      const apiKeyId = data['llm_config.api_key_id'] as string;
      if (!apiKeyId) {
        return [];
      }
      try {
        // Get service from selected API key
        const { data: apiKeysData } = await apolloClient.query<GetApiKeysQuery>({
          query: GetApiKeysDocument,
          fetchPolicy: 'network-only'  // Always fetch fresh data to avoid stale API keys
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
          },
          fetchPolicy: 'network-only'
        });
        
        if (!modelsData || !modelsData.available_models) {
          console.warn('No models data received from API');
          return [];
        }
        return modelsData.available_models.map((model: string) => ({
          value: model,
          label: model
        }));
      } catch (error) {
        console.error('Failed to fetch models:', error);
        return [];
      }
    }
  },
  {
    name: 'temperature' as keyof ExtendedPersonData & string,
    type: 'number',
    label: 'Temperature',
    placeholder: '0.7',
    min: 0,
    max: 2,
    column: 1
  },
  {
    name: 'llm_config.system_prompt' as keyof ExtendedPersonData & string,
    type: 'textarea',
    label: 'System Prompt',
    placeholder: 'Enter system prompt',
    rows: 4,
    column: 2
  }
];

/**
 * Person panel configuration
 */
export const PersonPanelConfig: PanelLayoutConfig<ExtendedPersonData> = {
  layout: 'twoColumn',
  leftColumn: personFields.filter(f => f.column === 1),
  rightColumn: personFields.filter(f => f.column === 2)
};