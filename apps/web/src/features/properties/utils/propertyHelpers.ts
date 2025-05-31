/**
 * Property panel utility functions
 */

import { useConsolidatedDiagramStore } from '@/shared/stores';
import { API_ENDPOINTS } from '@/shared/utils/apiConfig';

export const formatPropertyValue = (value: any, type: string): string => {
  if (value === null || value === undefined) {
    return '';
  }

  switch (type) {
    case 'boolean':
      return value ? 'true' : 'false';
    case 'number':
      return Number(value).toString();
    case 'array':
      return Array.isArray(value) ? value.join(', ') : '';
    case 'object':
      return typeof value === 'object' ? JSON.stringify(value, null, 2) : '';
    default:
      return String(value);
  }
};

export const parsePropertyValue = (value: string, type: string): any => {
  if (!value) {
    return type === 'boolean' ? false : type === 'number' ? 0 : '';
  }

  switch (type) {
    case 'boolean':
      return value.toLowerCase() === 'true';
    case 'number': {
      const num = Number(value);
      return isNaN(num) ? 0 : num;
    }
    case 'array':
      return value.split(',').map(item => item.trim()).filter(Boolean);
    case 'object':
      try {
        return JSON.parse(value);
      } catch {
        return {};
      }
    default:
      return value;
  }
};

export const getPropertyDisplayName = (key: string): string => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

export const shouldShowProperty = (key: string, value: any): boolean => {
  // Hide internal properties
  if (key.startsWith('_') || key.startsWith('__')) {
    return false;
  }

  // Hide undefined/null values for optional properties
  if (value === undefined || value === null) {
    return false;
  }

  return true;
};

/**
 * Get API key options for select fields
 * This function accesses the store directly to get the current API keys
 */
export const getApiKeyOptions = (): Array<{ value: string; label: string }> => {
  // We need to access the store directly since this is called from config
  // Use the store's getState method to access current state
  const store = useConsolidatedDiagramStore.getState();
  const apiKeys = store.apiKeys || [];
  
  return apiKeys.map(apiKey => ({
    value: apiKey.id,
    label: `${apiKey.name} (${apiKey.service})`
  }));
};

/**
 * Get model options for select fields
 * Fetches available models from the backend API
 */
export const getModelOptions = async (): Promise<Array<{ value: string; label: string }>> => {
  try {
    const response = await fetch(API_ENDPOINTS.MODELS);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch models: ${response.status}`);
    }
    
    const data = await response.json();
    
    // If providers data is available, use that to create options
    if (data.providers) {
      const options: Array<{ value: string; label: string }> = [];
      
      Object.entries(data.providers).forEach(([provider, models]) => {
        if (Array.isArray(models)) {
          models.forEach((model: string) => {
            options.push({
              value: model,
              label: `${model} (${provider})`
            });
          });
        }
      });
      
      return options;
    }
    
    // If specific models are returned, use those
    if (data.models && Array.isArray(data.models)) {
      return data.models.map((model: string) => ({
        value: model,
        label: model
      }));
    }
    
    // Fallback to empty array if no models found
    return [];
    
  } catch (error) {
    console.error('Failed to fetch models from API:', error);
    
    // Fallback to default models on error
    return [
      // OpenAI models
      { value: 'gpt-4o', label: 'GPT-4o (OpenAI)' },
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini (OpenAI)' },
      { value: 'gpt-4-turbo', label: 'GPT-4 Turbo (OpenAI)' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (OpenAI)' },
      
      // Claude models
      { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (Anthropic)' },
      { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Anthropic)' },
      { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus (Anthropic)' },
      
      // Gemini models
      { value: 'gemini-1.5-pro-latest', label: 'Gemini 1.5 Pro (Google)' },
      { value: 'gemini-1.5-flash-latest', label: 'Gemini 1.5 Flash (Google)' },
      
      // Grok models
      { value: 'grok-beta', label: 'Grok Beta (xAI)' },
    ];
  }
};