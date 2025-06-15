/**
 * Centralized API client for all HTTP requests
 * Provides consistent error handling, caching, and type safety
 */

import { toast } from 'sonner';
import { API_ENDPOINTS, getApiUrl, ApiCache, apiCache } from './config';
import { 
  createErrorHandlerFactory,
  type DomainApiKey,
  type DomainDiagram
} from '@/types';
import type {
  RequestConfig,
  ApiResponse,
  ApiClientOptions
} from '@/types/api';

// Internal types for backwards compatibility
interface CacheConfig {
  key?: string;
  ttl?: number;
}

interface InternalRequestConfig extends RequestConfig {
  cacheConfig?: CacheConfig;
  skipErrorToast?: boolean;
  errorContext?: string;
}


class Client {
  private options: ApiClientOptions;
  private createErrorHandler = createErrorHandlerFactory('Client');

  constructor(options: ApiClientOptions = {}) {
    this.options = {
      baseURL: getApiUrl(''),
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };
  }

  /**
   * Generic request method that returns ApiResponse<T>
   */
  private async request<T>(
    endpoint: string,
    options: Partial<InternalRequestConfig> = {}
  ): Promise<ApiResponse<T>> {
    const {
      query,
      body,
      method = 'GET',
      headers = {},
      signal,
      cacheConfig,
      skipErrorToast = false,
      errorContext = 'API Request'
    } = options;

    // Check cache first if configured
    if (cacheConfig?.key && method === 'GET') {
      const cachedData = apiCache.get<T>(cacheConfig.key);
      if (cachedData !== null) {
        return {
          success: true,
          data: cachedData
        };
      }
    }

    // Build URL with query parameters
    let url = this.options.baseURL ? this.options.baseURL + endpoint : getApiUrl(endpoint);
    if (query) {
      const searchParams = new URLSearchParams();
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    const controller = new AbortController();
    const timeoutId = this.options.timeout 
      ? setTimeout(() => controller.abort(), this.options.timeout)
      : null;

    try {
      const response = await fetch(url, {
        method,
        headers: {
          ...this.options.headers,
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: signal || controller.signal
      });

      if (timeoutId) clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        const errorMessage = this.parseErrorMessage(errorText, response.status);
        if (!skipErrorToast) {
          toast.error(`${errorContext}: ${errorMessage}`);
        }
        return {
          success: false,
          error: errorMessage
        };
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
      if (cacheConfig?.key && method === 'GET') {
        apiCache.set(cacheConfig.key, data, cacheConfig.ttl);
      }

      // Add metadata if available
      const result: ApiResponse<T> = {
        success: true,
        data
      };

      // Check for filename/path in response headers or data
      const contentDisposition = response.headers.get('content-disposition');
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);;
        if (filenameMatch) {
          (result as any).filename = filenameMatch[1];
        }
      }

      return result;
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId);
      
      const errorMessage = error instanceof Error 
        ? (error.name === 'AbortError' ? 'Request timeout' : error.message)
        : 'An unknown error occurred';
      
      if (!skipErrorToast) {
        this.createErrorHandler(error as Error);
        toast.error(`${errorContext}: ${errorMessage}`);
      }
      
      return {
        success: false,
        error: errorMessage
      };
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
  async get<T>(endpoint: string, options?: Partial<InternalRequestConfig>): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
    if (!response.success) {
      throw new Error(response.error);
    }
    return response.data;
  }

  /**
   * POST request
   */
  async post<T, D = unknown>(
    endpoint: string,
    data?: D,
    options?: Partial<InternalRequestConfig>
  ): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data as any,
    });
    if (!response.success) {
      throw new Error(response.error);
    }
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T, D = unknown>(
    endpoint: string,
    data?: D,
    options?: Partial<InternalRequestConfig>
  ): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data as any,
    });
    if (!response.success) {
      throw new Error(response.error);
    }
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T = void>(endpoint: string, options?: Partial<InternalRequestConfig>): Promise<T> {
    const response = await this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
    if (!response.success) {
      throw new Error(response.error);
    }
    return response.data;
  }

  /**
   * Upload file - special handling for FormData
   */
  async uploadFile(
    endpoint: string,
    file: File,
    additionalData?: Record<string, string>,
    options?: Partial<InternalRequestConfig>
  ): Promise<{ filename: string }> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const { skipErrorToast = false, errorContext = 'Upload File' } = options || {};
    const url = this.options.baseURL ? this.options.baseURL + endpoint : getApiUrl(endpoint);
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        const errorMessage = this.parseErrorMessage(errorText, response.status);
        if (!skipErrorToast) {
          toast.error(`${errorContext}: ${errorMessage}`);
        }
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      if (!skipErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        toast.error(`${errorContext}: ${errorMessage}`);
      }
      throw error;
    }
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
      query: { service, api_key_id: apiKeyId },
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
): Promise<ApiResponse<{ path: string }>> => {
  try {
    const data = await apiClient.post<{ path: string }>(
      API_ENDPOINTS.SAVE_DIAGRAM,
      { diagram, filename },
      { errorContext: 'Save Diagram' }
    );
    return { success: true, data };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Save failed' 
    };
  }
};

export const convertDiagram = async (
  content: string,
  fromFormat: string,
  toFormat: string
): Promise<ApiResponse<{ content: string; format: string }>> => {
  try {
    // Backend returns { success: boolean, output: string, message: string }
    const data = await apiClient.post<any>(
      API_ENDPOINTS.DIAGRAMS_CONVERT,
      { content, from_format: fromFormat, to_format: toFormat },
      { errorContext: 'Convert Diagram' }
    );
    // Map backend response to expected format
    return { 
      success: true, 
      data: {
        content: data.output || data.content || '',
        format: data.format || toFormat
      }
    };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Convert failed' 
    };
  }
};

export const uploadFile = async (file: File): Promise<ApiResponse<{ filename: string; content: string }>> => {
  try {
    const response = await apiClient.uploadFile(
      API_ENDPOINTS.UPLOAD_FILE,
      file,
      undefined,
      { errorContext: 'Upload File' }
    );
    return { success: true, data: { ...response, content: '' } };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Upload failed' 
    };
  }
};

export const checkHealth = async (): Promise<boolean> => {
  try {
    await apiClient.get<{ status: string }>(API_ENDPOINTS.HEALTH, { skipErrorToast: true });
    return true;
  } catch {
    return false;
  }
};

export const getExecutionCapabilities = async (): Promise<ApiResponse<{ 
  supported_node_types: string[]; 
  features: { [key: string]: boolean } 
}>> => {
  try {
    const data = await apiClient.get<{ 
      supported_node_types: string[]; 
      features: { [key: string]: boolean } 
    }>(API_ENDPOINTS.EXECUTION_CAPABILITIES, {
      errorContext: 'Fetch Capabilities',
    });
    return { success: true, data };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Fetch failed' 
    };
  }
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
          query: filters,
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