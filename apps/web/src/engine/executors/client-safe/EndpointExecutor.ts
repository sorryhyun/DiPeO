/**
 * Endpoint node executor - handles output and finalization
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/core';

import { ClientSafeExecutor } from '../base-executor';
import { getApiUrl } from '@/shared/utils/apiConfig';

export class EndpointExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    // Endpoint nodes should have incoming connections
    const incomingArrows = context.incomingArrows[node.id] || [];
    if (incomingArrows.length === 0) {
      return {
        isValid: false,
        errors: ['Endpoint nodes should have at least one incoming connection']
      };
    }

    return { isValid: true, errors: [] };
  }

  async execute(node: Node, context: TypedExecutionContext, _options?: Record<string, unknown>): Promise<ExecutorResult> {
    const inputs = this.getInputValues(node, context);
    const outputFormat = this.getNodeProperty(node, 'outputFormat', 'json');
    const saveToFile = this.getNodeProperty(node, 'saveToFile', false);
    
    try {
      const output = this.formatOutput(inputs, outputFormat, node);
      
      // If saveToFile is enabled, call server API for file saving
      if (saveToFile) {
        const filePath = this.getNodeProperty(node, 'filePath', '');
        const fileFormat = this.getNodeProperty(node, 'fileFormat', 'text');
        
        if (filePath) {
          await this.saveToFile(node, output, filePath, fileFormat);
        }
      }
      
      return this.createSuccessResult(output, 0, {
        outputFormat,
        inputCount: Object.keys(inputs).length,
        finalizedAt: new Date().toISOString(),
        isEndpoint: true,
        savedToFile: saveToFile,
        filePath: saveToFile ? this.getNodeProperty(node, 'filePath', '') : undefined
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to execute endpoint: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { outputFormat, inputs, error: error instanceof Error ? error.message : String(error) }
      );
    }
  }

  /**
   * Format the output according to the specified format
   */
  private formatOutput(inputs: Record<string, unknown>, format: string, node: Node): string | Record<string, unknown> {
    switch (format.toLowerCase()) {
      case 'json':
        return this.formatAsJSON(inputs);
      case 'text':
        return this.formatAsText(inputs, node);
      case 'csv':
        return this.formatAsCSV(inputs);
      case 'raw':
        return this.formatAsRaw(inputs) as string | Record<string, unknown>;
      default:
        return inputs; // Default to raw inputs
    }
  }

  private formatAsJSON(inputs: Record<string, unknown>): string {
    return JSON.stringify(inputs, null, 2);
  }

  private formatAsText(inputs: Record<string, unknown>, node: Node): string {
    const template = this.getNodeProperty<string>(node, 'textTemplate', '');
    
    if (template) {
      // Apply template with inputs
      let result: string = template;
      for (const [key, value] of Object.entries(inputs)) {
        const regex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
        result = result.replace(regex, String(value));
      }
      return result;
    }

    // Default text format
    return Object.entries(inputs)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');
  }

  private formatAsCSV(inputs: Record<string, unknown>): string {
    // Simple CSV format - assumes inputs contain arrays or objects
    const firstValue = Object.values(inputs)[0];
    
    if (Array.isArray(firstValue) && firstValue.length > 0 && typeof firstValue[0] === 'object') {
      // Array of objects -> CSV
      const headers = Object.keys(firstValue[0]);
      const csvRows = [
        headers.join(','),
        ...firstValue.map(row => 
          headers.map(header => JSON.stringify(row[header] || '')).join(',')
        )
      ];
      return csvRows.join('\n');
    }

    // Fallback: convert inputs to simple CSV
    const headers = Object.keys(inputs);
    const values = Object.values(inputs);
    return `${headers.join(',')}\n${values.map(v => JSON.stringify(v)).join(',')}`;
  }

  private formatAsRaw(inputs: Record<string, unknown>): unknown {
    // Return the first input value if there's only one, otherwise return all inputs
    const values = Object.values(inputs);
    return values.length === 1 ? values[0] : inputs;
  }

  /**
   * Save output to file via server API
   */
  private async saveToFile(node: Node, output: unknown, filePath: string, fileFormat: string): Promise<void> {
    const payload = {
      content: output,
      save_to_file: true,
      file_path: filePath,
      file_format: fileFormat
    };

    const response = await fetch(getApiUrl('/api/nodes/endpoint/execute'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw this.createExecutionError(
        `File save API call failed: ${response.status} ${errorText}`,
        node,
        { 
          filePath,
          fileFormat,
          status: response.status,
          error: errorText
        }
      );
    }
  }
}