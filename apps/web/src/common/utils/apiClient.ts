/**
 * Centralized API client for all HTTP requests
 * Provides consistent error handling, caching, and type safety
 */

import { toast } from 'sonner';
import { API_ENDPOINTS, getApiUrl } from './apiConfig';
import { apiCache, ApiCache } from './apiCache';
import { createErrorHandlerFactory } from '@/common/types';

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

interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

class ApiClient {
  private defaultHeaders = {
    'Content-Type': 'application/json',
  };

  private createErrorHandler = createErrorHandlerFactory(toast);

  /**
   * Generic request method with error handling and caching
   */
  private async request<T>(
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<ApiResponse<T>> {
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

    const errorHandler = this.createErrorHandler(errorContext);

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
export const apiClient = new ApiClient();

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