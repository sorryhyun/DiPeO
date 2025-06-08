import { apiClient } from '@/utils/api/client';
import { validateDiagramResponse, validateDiagramForExecution } from './validators';
import { DomainDiagram } from '@/types/domain';
import { ValidationError, isZodError } from './errors';

/**
 * Enhanced API client with validation
 */
export class ValidatedApiClient {
  /**
   * Load and validate a diagram
   */
  async loadDiagram(id: string): Promise<DomainDiagram> {
    try {
      const response = await apiClient.get(`/diagrams/${id}`);
      
      // Validate response data
      const validated = validateDiagramResponse(response.data);
      
      // Additional business logic validation
      validateDiagramForExecution(validated);
      
      return validated;
    } catch (error) {
      if (isZodError(error)) {
        console.error('Diagram validation failed:', error.errors);
        throw new ValidationError('Invalid diagram format received from server');
      }
      throw error;
    }
  }

  /**
   * Save diagram with validation
   */
  async saveDiagram(diagram: DomainDiagram): Promise<{ id: string }> {
    try {
      // Validate before sending
      validateDiagramResponse(diagram);
      
      const response = await apiClient.post('/diagrams', diagram);
      return response.data;
    } catch (error) {
      if (isZodError(error)) {
        throw new ValidationError('Invalid diagram format');
      }
      throw error;
    }
  }

  /**
   * Convert diagram format with validation
   */
  async convertDiagram(data: unknown, format: string): Promise<DomainDiagram> {
    try {
      const response = await apiClient.post('/diagrams/convert', {
        data,
        format
      });
      
      // Validate converted diagram
      return validateDiagramResponse(response.data);
    } catch (error) {
      if (isZodError(error)) {
        throw new ValidationError('Conversion resulted in invalid diagram format');
      }
      throw error;
    }
  }

  /**
   * Get execution capabilities with validation
   */
  async getExecutionCapabilities(): Promise<{
    features: string[];
    nodeTypes: string[];
    controls: string[];
  }> {
    const response = await apiClient.get('/execution-capabilities');
    
    // Simple validation for capabilities
    if (!response.data.features || !Array.isArray(response.data.features)) {
      throw new ValidationError('Invalid execution capabilities format');
    }
    
    return response.data;
  }
}

// Export singleton instance
export const validatedApi = new ValidatedApiClient();