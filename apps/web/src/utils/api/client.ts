/**
 * Centralized API client for all HTTP requests
 * Provides consistent error handling, caching, and type safety
 */

import { toast } from 'sonner';
import { API_ENDPOINTS, getApiUrl, ApiCache, apiCache } from './config';
import { 
  createErrorHandlerFactory,
  type DomainApiKey,
  type DomainDiagram,
  type ApiResponse as ApiResponseType
} from '@/types';

// Internal HTTP response wrapper
interface HttpResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

// Types
/* global RequestInit */
interface ApiRequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
  cacheConfig?: {
    key?: string;
    ttl?: number;
  };
  skipErrorToast?: boolean;
  errorContext?: string;
}


class Client {
  private defaultHeaders = {
    'Content-Type': 'application/json',
  };

  private createErrorHandler = createErrorHandlerFactory('Client');

  /**
   * Generic request method with error handling and caching
   */
  private async request<T>(
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<HttpResponse<T>> {
    const {
      params,
      cacheConfig,
      skipErrorToast = false,
      errorContext = 'API Request',
      headers = {},
      ...fetchOptions
    } = options;

    // Check cache first if configured
    if (cacheConfig?.key && fetchOptions.method === 'GET') {
      const cachedData = apiCache.get<T>(cacheConfig.key);
      if (cachedData !== null) {
        return {
          data: cachedData,
          status: 200,
          headers: new Headers(),
        };
      }
    }

    // Build URL with query parameters
    let url = getApiUrl(endpoint);
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value));
      });
      url += `?${searchParams.toString()}`;
    }

    const errorHandler = (error: Error) => {
      this.createErrorHandler(error);
      if (!skipErrorToast) {
        toast.error(`${errorContext}: ${error.message}`);
      }
    };

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers: {
          ...this.defaultHeaders,
          ...headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        const errorMessage = this.parseErrorMessage(errorText, response.status);
        throw new Error(errorMessage);
      }

      // Parse response based on content type
      const contentType = response.headers.get('content-type');
      let data: T;

      if (contentType?.includes('application/json')) {
        data = await response.json();
      } else if (contentType?.includes('text/')) {
        data = (await response.text()) as T;
      } else {
        // For other content types, return the response as-is
        data = response as unknown as T;
      }

      // Cache if configured
      if (cacheConfig?.key && fetchOptions.method === 'GET') {
        apiCache.set(cacheConfig.key, data, cacheConfig.ttl);
      }

      return {
        data,
        status: response.status,
        headers: response.headers,
      };
    } catch (error) {
      if (!skipErrorToast) {
        errorHandler(error as Error);
      }
      throw error;
    }
  }

  /**
   * Parse error message from response
   */
  private parseErrorMessage(errorText: string, status: number): string {
    try {
      const errorData = JSON.parse(errorText);
      return errorData.detail || errorData.message || `Request failed with status ${status}`;
    } catch {
      return errorText || `Request failed with status ${status}`;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
    return response.data;
  }

  /**
   * POST request
   */
  async post<T, D = unknown>(
    endpoint: string,
    data?: D,
    options?: ApiRequestOptions
  ): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T, D = unknown>(
    endpoint: string,
    data?: D,
    options?: ApiRequestOptions
  ): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T = void>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
    return response.data;
  }

  /**
   * Upload file
   */
  async uploadFile(
    endpoint: string,
    file: File,
    additionalData?: Record<string, string>,
    options?: ApiRequestOptions
  ): Promise<{ filename: string }> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const response = await this.request<{ filename: string }>(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData - browser will set it with boundary
      },
    });

    return response.data;
  }
}

// Export singleton instance
export const apiClient = new Client();

// Legacy functional exports for backward compatibility
export const fetchApiKeys = async (): Promise<DomainApiKey[]> => {
  return apiClient.get<DomainApiKey[]>(API_ENDPOINTS.API_KEYS, {
    errorContext: 'Load API Keys',
  });
};

export const getApiKeyOptions = (): Array<{ value: string; label: string }> => {
  // This should be called from a React component using useApiKeyStore
  // For now, return empty array and let the component handle this
  const apiKeys: DomainApiKey[] = [];
  
  return apiKeys.map((apiKey: DomainApiKey) => ({
    value: apiKey.id,
    label: `${apiKey.label} (${apiKey.service})`
  }));
};

export const fetchAvailableModels = async (
  service: string,
  apiKeyId: string
): Promise<Array<{ value: string; label: string }>> => {
  const cacheKey = ApiCache.getModelListKey(service, apiKeyId);
  const cachedModels = apiCache.get<Array<{ value: string; label: string }>>(cacheKey);
  if (cachedModels) {
    return cachedModels;
  }

  const data = await apiClient.get<{ models?: string[]; error?: string }>(
    API_ENDPOINTS.MODELS(apiKeyId),
    {
      params: { service, api_key_id: apiKeyId },
      errorContext: 'Fetch Models',
    }
  );
  
  if (data.error || !data.models) {
    return [];
  }
  
  const modelOptions = data.models.map((model: string) => ({
    value: model,
    label: model
  }));
  
  apiCache.set(cacheKey, modelOptions);
  return modelOptions;
};

export const preInitializeModel = async (
  service: string,
  model: string,
  apiKeyId: string
): Promise<boolean> => {
  try {
    const data = await apiClient.post<{ success: boolean }>(
      API_ENDPOINTS.INITIALIZE_MODEL,
      { service, model, api_key_id: apiKeyId },
      { errorContext: 'Initialize Model', skipErrorToast: true }
    );
    return data.success || false;
  } catch {
    return false;
  }
};

export const saveDiagram = async (
  diagram: DomainDiagram,
  filename: string
): Promise<ApiResponseType<{ path: string }>> => {
  const data = await apiClient.post<{ path: string }>(
    API_ENDPOINTS.SAVE_DIAGRAM,
    { diagram, filename },
    { errorContext: 'Save Diagram' }
  );
  
  return { data, success: true };
};

export const convertDiagram = async (
  content: string,
  fromFormat: string,
  toFormat: string
): Promise<ApiResponseType<{ content: string; format: string }>> => {
  const data = await apiClient.post<{ content: string; format: string }>(
    API_ENDPOINTS.DIAGRAMS_CONVERT,
    { content, from_format: fromFormat, to_format: toFormat },
    { errorContext: 'Convert Diagram' }
  );
  
  return { data, success: true };
};

export const uploadFile = async (file: File): Promise<ApiResponseType<{ filename: string; content: string }>> => {
  const response = await apiClient.uploadFile(
    API_ENDPOINTS.UPLOAD_FILE,
    file,
    undefined,
    { errorContext: 'Upload File' }
  );
  return { data: { ...response, content: '' }, success: true };
};

export const checkHealth = async (): Promise<boolean> => {
  try {
    await apiClient.get<{ status: string }>(API_ENDPOINTS.HEALTH, { skipErrorToast: true });
    return true;
  } catch {
    return false;
  }
};

export const getExecutionCapabilities = async (): Promise<ApiResponseType<{ 
  supported_node_types: string[]; 
  features: { [key: string]: boolean } 
}>> => {
  const data = await apiClient.get<{ 
    supported_node_types: string[]; 
    features: { [key: string]: boolean } 
  }>(API_ENDPOINTS.EXECUTION_CAPABILITIES, {
    errorContext: 'Fetch Capabilities',
  });
  return { data, success: true };
};

// Convenience methods for common endpoints
export const api = {
  // API Key management
  apiKeys: {
    list: () => 
      apiClient.get<Array<{ id: string; name: string; service: string }>>(
        API_ENDPOINTS.API_KEYS,
        { errorContext: 'Load API Keys' }
      ),
    
    delete: (id: string) =>
      apiClient.delete(API_ENDPOINTS.API_KEY_BY_ID(id), {
        errorContext: 'Delete API Key',
      }),
    
    getModels: (id: string, service: string) =>
      apiClient.get<{ models: Array<{ id: string; name: string }> }>(
        API_ENDPOINTS.MODELS(id),
        {
          cacheConfig: {
            key: ApiCache.getModelListKey(service, id),
            ttl: 5 * 60 * 1000, // 5 minutes
          },
          errorContext: 'Load Models',
        }
      ),
  },

  // Model initialization
  initializeModel: (data: { service: string; model: string; apiKeyId: string }) =>
    apiClient.post<{ success: boolean }>(
      API_ENDPOINTS.INITIALIZE_MODEL,
      data,
      { errorContext: 'Initialize Model' }
    ),

  // Conversations
  conversations: {
    list: (filters?: { execution_id?: string; person_id?: string }) =>
      apiClient.get<Array<{ id: string; messages: unknown[] }>>(
        API_ENDPOINTS.CONVERSATIONS,
        { 
          params: filters,
          errorContext: 'Load Conversations',
        }
      ),
  },

  // Diagram operations
  diagrams: {
    save: (data: { diagram: unknown; filename: string }) =>
      apiClient.post<{ message: string; filename: string }>(
        API_ENDPOINTS.SAVE_DIAGRAM,
        data,
        { errorContext: 'Save Diagram' }
      ),

    importYaml: (content: string) =>
      apiClient.post<{ diagram: unknown }>(
        API_ENDPOINTS.IMPORT_YAML,
        { content },
        { errorContext: 'Import YAML' }
      ),

    capabilities: () =>
      apiClient.get<{ supportedNodeTypes: string[]; features: string[] }>(
        API_ENDPOINTS.EXECUTION_CAPABILITIES,
        { 
          cacheConfig: { key: 'execution-capabilities', ttl: 10 * 60 * 1000 },
          errorContext: 'Load Capabilities',
        }
      ),
  },

  // File operations
  uploadFile: (file: File, type?: string) =>
    apiClient.uploadFile(
      API_ENDPOINTS.UPLOAD_FILE,
      file,
      type ? { type } : undefined,
      { errorContext: 'Upload File' }
    ),

  // Health check
  health: () =>
    apiClient.get<{ status: string }>(
      API_ENDPOINTS.HEALTH,
      { skipErrorToast: true }
    ),
};