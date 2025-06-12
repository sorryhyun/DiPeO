/**
 * Typed API methods using request/response interfaces from @/types/api
 */

import { apiClient } from './client';
import { API_ENDPOINTS } from './config';
import type {
  ApiResponse,
  DiagramSaveRequest,
  DiagramSaveResponse,
  ConvertRequest,
  ConvertResponse,
  HealthResponse,
  ExecutionCapabilitiesResponse
} from '@/types/api';

/**
 * Typed API methods that properly use the request/response interfaces
 */
export const typedApi = {
  /**
   * Save a diagram to the backend
   */
  async saveDiagram(request: DiagramSaveRequest): Promise<ApiResponse<DiagramSaveResponse>> {
    try {
      const data = await apiClient.post<DiagramSaveResponse>(
        API_ENDPOINTS.SAVE_DIAGRAM,
        request,
        { errorContext: 'Save Diagram' }
      );
      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Save failed'
      };
    }
  },

  /**
   * Convert diagram between formats
   */
  async convertDiagram(request: ConvertRequest): Promise<ApiResponse<ConvertResponse>> {
    try {
      const data = await apiClient.post<ConvertResponse>(
        API_ENDPOINTS.DIAGRAMS_CONVERT,
        {
          content: request.content,
          from_format: request.sourceFormat,
          to_format: request.targetFormat
        },
        { errorContext: 'Convert Diagram' }
      );
      
      // Map backend response to match ConvertResponse interface
      return {
        success: true,
        data: {
          converted: data.converted || data.content || '',
          format: data.format || request.targetFormat
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Convert failed'
      };
    }
  },

  /**
   * Check API health status
   */
  async checkHealth(): Promise<ApiResponse<HealthResponse>> {
    try {
      const data = await apiClient.get<HealthResponse>(
        API_ENDPOINTS.HEALTH,
        { skipErrorToast: true }
      );
      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Health check failed'
      };
    }
  },

  /**
   * Get execution capabilities
   */
  async getExecutionCapabilities(): Promise<ApiResponse<ExecutionCapabilitiesResponse>> {
    try {
      const data = await apiClient.get<any>(
        API_ENDPOINTS.EXECUTION_CAPABILITIES,
        { errorContext: 'Fetch Capabilities' }
      );
      
      // Map backend response to match ExecutionCapabilitiesResponse interface
      return {
        success: true,
        data: {
          node_types: data.supported_node_types || data.node_types || [],
          features: {
            real_time_control: data.features?.real_time_control ?? false,
            interactive_prompts: data.features?.interactive_prompts ?? false,
            memory_support: data.features?.memory_support ?? false,
            forgetting_rules: data.features?.forgetting_rules ?? false,
            ...data.features
          },
          supported_languages: data.supported_languages
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Fetch capabilities failed'
      };
    }
  }
};

/**
 * Helper to handle ApiResponse results
 */
export function handleApiResponse<T>(
  response: ApiResponse<T>,
  onSuccess: (data: T) => void,
  onError?: (error: string) => void
): void {
  if (response.success) {
    onSuccess(response.data);
  } else if (onError) {
    onError(response.error);
  }
}