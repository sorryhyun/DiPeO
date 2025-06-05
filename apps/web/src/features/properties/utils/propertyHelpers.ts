/**
 * Property panel utility functions
 */

import { 
  getApiKeyOptions as getApiKeyOptionsFromClient,
  fetchAvailableModels,
  preInitializeModel as preInitializeModelClient 
} from '@/common/utils/api-client';

export const formatPropertyValue = (value: unknown, type: string): string => {
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

export const parsePropertyValue = (value: string, type: string): unknown => {
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

export const shouldShowProperty = (key: string, value: unknown): boolean => {
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
 * Delegates to centralized API client
 */
export const getApiKeyOptions = (): Array<{ value: string; label: string }> => {
  return getApiKeyOptionsFromClient();
};


/**
 * Get model options dynamically based on selected service and API key
 * Delegates to centralized API client
 */
export const getDynamicModelOptions = async (
  service?: string, 
  apiKeyId?: string
): Promise<Array<{ value: string; label: string }>> => {
  if (!service || !apiKeyId) {
    return [];
  }
  
  try {
    return await fetchAvailableModels(service, apiKeyId);
  } catch {
    return [];
  }
};

/**
 * Pre-initialize a model client on the backend for faster subsequent execution
 * Delegates to centralized API client
 */
export const preInitializeModel = async (
  service: string,
  model: string,
  apiKeyId: string
): Promise<boolean> => {
  console.log('[Person Property Panel] Pre-initializing model client:', {
    service,
    model,
    apiKeyId
  });
  
  return preInitializeModelClient(service, model, apiKeyId);
};

