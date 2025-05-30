import React, { useState, useEffect } from 'react';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { getApiUrl, API_ENDPOINTS } from '@/shared/utils/apiConfig';
import { type PersonDefinition, type ApiKey } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import { useApiKeys } from '../hooks/useApiKeys';
import {
  Form, FormRow,
  InlineTextField, InlineSelectField, TextAreaField
} from '../wrappers';

export const PersonPanelContent: React.FC<{ personId: string; data: PersonDefinition }> = ({ personId, data }) => {
  const { updatePerson } = useConsolidatedDiagramStore();
  const { formData, handleChange: updateData } = usePropertyPanel<PersonDefinition>(personId, 'person', data);

  // Use shared API keys hook
  const { apiKeysList, loading: loadingApiKeys, error: apiKeysError } = useApiKeys();

  // Models state
  const [modelOptions, setModelOptions] = useState<{ value: string; label: string }[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);

  // Effect for loading models
  useEffect(() => {
    if (!formData.service || !formData.apiKeyId) {
      setModelOptions([]);
      return;
    }
    setLoadingModels(true);
    setModelError(null);
    fetch(getApiUrl(`${API_ENDPOINTS.MODELS}?service=${formData.service}&api_key_id=${formData.apiKeyId}`))
      .then(res => res.json())
      .then(body => {
        if (body.error) {
          setModelError(body.error);
          setModelOptions([]);
        } else {
          setModelOptions(body.models.map((m: string) => ({ value: m, label: m })));
        }
      })
      .catch(err => setModelError(err.message))
      .finally(() => setLoadingModels(false));
  }, [formData.service, formData.apiKeyId]);

  const handleChange = (field: keyof PersonDefinition, value: any) => {
    updateData(field, value);
    updatePerson(personId, { [field]: value });
    
    // Clear model selection when service or API key changes
    if (field === 'service' || field === 'apiKeyId') {
      updateData('modelName', '');
      updatePerson(personId, { modelName: '' });
    }
  };

  const serviceOptions = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'claude', label: 'Claude' },
    { value: 'gemini', label: 'Gemini' },
    { value: 'grok', label: 'Grok' },
    { value: 'custom', label: 'Custom' }
  ];

  const apiKeyOptions = (apiKeysList || [])
    .filter(k => k.service === formData.service)
    .map(key => ({ value: key.id, label: key.name }));

  return (
    <Form>
      <div className="space-y-4">
        <FormRow>
          <InlineTextField
            label="Person Name"
            value={formData.label || ''}
            onChange={(v) => handleChange('label', v)}
            placeholder="Person Name"
            className="flex-1"
          />
          <InlineSelectField
            label="Service"
            value={formData.service || ''}
            onChange={(v) => handleChange('service', v)}
            options={serviceOptions}
            className="flex-1"
          />
        </FormRow>

        <FormRow>
          <InlineSelectField
            label="API Key"
            value={formData.apiKeyId || ''}
            onChange={(v) => handleChange('apiKeyId', v)}
            options={apiKeyOptions}
            placeholder="Select API Key"
            loading={loadingApiKeys}
            error={apiKeysError}
            className="flex-1"
          />
          <InlineSelectField
            label="Model"
            value={formData.modelName || ''}
            onChange={(v) => handleChange('modelName', v)}
            options={modelOptions}
            placeholder="Select Model"
            loading={loadingModels}
            error={modelError}
            disabled={modelOptions.length === 0}
            className="flex-1"
          />
        </FormRow>

        <TextAreaField
          label="System Prompt"
          value={formData.systemPrompt || ''}
          onChange={(v) => handleChange('systemPrompt', v)}
          placeholder="Enter system prompt"
        />
      </div>
    </Form>
  );
};