/**
 * Centralized API client
 * All API calls should go through this module
 */

import { type ApiKey, type Diagram, type ApiResponse } from '@/common/types';
import { getApiUrl, API_ENDPOINTS } from './apiConfig';
import { apiCache } from './apiCache';
import { useApiKeyStore } from '@/state/stores';

/**
 * Fetch API keys from backend
 */
export const fetchApiKeys = async (): Promise<ApiKey[]> => {
  const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
  
  if (!response.ok) {
    throw new Error('Failed to load API keys');
  }
  
  const body = await response.json();
  return Array.isArray(body) ? body : [];
};

/**
 * Get API key options for select fields
 * This uses the store to get current API keys without fetching
 */
export const getApiKeyOptions = (): Array<{ value: string; label: string }> => {
  const store = useApiKeyStore.getState();
  const apiKeys = store.apiKeys || [];
  
  return apiKeys.map(apiKey => ({
    value: apiKey.id,
    label: `${apiKey.name} (${apiKey.service})`
  }));
};

/**
 * Fetch available models for a specific service and API key
 */
export const fetchAvailableModels = async (
  service: string,
  apiKeyId: string
): Promise<Array<{ value: string; label: string }>> => {
  // Check cache first
  const cacheKey = `models:${service}:${apiKeyId}`;
  const cachedModels = apiCache.get<Array<{ value: string; label: string }>>(cacheKey);
  if (cachedModels) {
    return cachedModels;
  }

  const params = new URLSearchParams();
  params.append('service', service);
  params.append('api_key_id', apiKeyId);
  
  const url = `${getApiUrl(API_ENDPOINTS.MODELS(apiKeyId))}?${params.toString()}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.status}`);
  }
  
  const data = await response.json();
  
  if (data.error) {
    return [];
  }
  
  if (data.models && Array.isArray(data.models)) {
    const modelOptions = data.models.map((model: string) => ({
      value: model,
      label: model
    }));
    
    // Cache the results
    apiCache.set(cacheKey, modelOptions);
    
    return modelOptions;
  }
  
  return [];
};

/**
 * Pre-initialize a model client on the backend
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
      return false;
    }

    const data = await response.json();
    return data.success || false;
  } catch {
    return false;
  }
};

/**
 * Save diagram to backend
 */
export const saveDiagram = async (
  diagram: Diagram,
  filename: string
): Promise<ApiResponse<{ path: string }>> => {
  const response = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      diagram,
      filename,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to save diagram');
  }

  return response.json();
};

/**
 * Convert diagram between formats
 */
export const convertDiagram = async (
  content: string,
  fromFormat: string,
  toFormat: string
): Promise<ApiResponse<{ content: string; format: string }>> => {
  const response = await fetch(getApiUrl(API_ENDPOINTS.DIAGRAMS_CONVERT), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content,
      from_format: fromFormat,
      to_format: toFormat,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to convert diagram');
  }

  return response.json();
};

/**
 * Upload file to backend
 */
export const uploadFile = async (file: File): Promise<ApiResponse<{ filename: string; content: string }>> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(getApiUrl(API_ENDPOINTS.UPLOAD_FILE), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to upload file');
  }

  return response.json();
};

/**
 * Check backend health
 */
export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(getApiUrl(API_ENDPOINTS.HEALTH));
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Get execution capabilities from backend
 */
export const getExecutionCapabilities = async (): Promise<ApiResponse<{ 
  supported_node_types: string[]; 
  features: { [key: string]: boolean } 
}>> => {
  const response = await fetch(getApiUrl(API_ENDPOINTS.EXECUTION_CAPABILITIES));
  
  if (!response.ok) {
    throw new Error('Failed to fetch execution capabilities');
  }

  return response.json();
};