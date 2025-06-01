/**
 * Property panel utility functions
 */

import { useConsolidatedDiagramStore } from '@/core/stores';
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';

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
    
    // Return empty array on error - no confusing fallback models
    return [];
  }
};

/**
 * Get model options dynamically based on selected service and API key
 * This fetches real available models from the API provider
 */
export const getDynamicModelOptions = async (
  service?: string, 
  apiKeyId?: string
): Promise<Array<{ value: string; label: string }>> => {
  // If no service or API key provided, return empty array
  if (!service || !apiKeyId) {
    return [];
  }

  try {
    // Build query parameters
    const params = new URLSearchParams();
    params.append('service', service);
    params.append('api_key_id', apiKeyId);
    
    const url = `${getApiUrl(API_ENDPOINTS.MODELS)}?${params.toString()}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch models: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Handle error response from backend
    if (data.error) {
      console.warn(`API returned error: ${data.error}`);
      return [];
    }
    
    // If specific models are returned, use those
    if (data.models && Array.isArray(data.models)) {
      return data.models.map((model: string) => ({
        value: model,
        label: model
      }));
    }
    
    // Return empty array if no models found
    return [];
    
  } catch (error) {
    console.error('Failed to fetch dynamic models from API:', error);
    return [];
  }
};

/**
 * Pre-initialize a model client on the backend for faster subsequent execution
 */
export const preInitializeModel = async (
  service: string,
  model: string,
  apiKeyId: string
): Promise<boolean> => {
  try {
    const response = await fetch(getApiUrl(API_ENDPOINTS.INITIALIZE_MODEL), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        service,
        model,
        api_key_id: apiKeyId,
      }),
    });

    if (!response.ok) {
      console.warn(`Failed to pre-initialize model: ${response.status}`);
      return false;
    }

    const data = await response.json();
    return data.success || false;
  } catch (error) {
    console.error('Error pre-initializing model:', error);
    return false;
  }
};

