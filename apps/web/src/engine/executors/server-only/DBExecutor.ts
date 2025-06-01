/**
 * DB executor - handles file I/O and database operations
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/core';

import { ServerOnlyExecutor } from '../base-executor';

export class DBExecutor extends ServerOnlyExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Validate operation type
    const operation = this.getNodeProperty(node, 'operation', '') as string;
    if (!operation) {
      errors.push('Database operation is required');
    }

    const validOperations = ['read', 'write', 'append', 'delete', 'list', 'query'];
    if (operation && !validOperations.includes(operation.toLowerCase())) {
      errors.push(`Invalid operation. Must be one of: ${validOperations.join(', ')}`);
    }

    // Validate file path for file operations
    if (['read', 'write', 'append', 'delete'].includes(operation.toLowerCase())) {
      const filePath = this.getNodeProperty(node, 'filePath', '');
      if (!filePath) {
        errors.push('File path is required for file operations');
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    const operation = this.getNodeProperty(node, 'operation', '').toLowerCase();
    const filePath = this.getNodeProperty(node, 'filePath', '');
    const inputs = this.getInputValues(node, context);
    
    try {
      const result = await this.executeDBOperation(operation, filePath, inputs, node);
      
      return this.createSuccessResult(result, 0, {
        operation,
        filePath,
        executedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to execute DB operation: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { operation, filePath, error: error instanceof Error ? error.message : String(error) }
      );
    }
  }

  /**
   * Execute database operation via backend API
   */
  private async executeDBOperation(
    operation: string,
    filePath: string,
    inputs: Record<string, any>,
    node: Node
  ): Promise<any> {
    // Call backend API for DB operation execution
    const payload = {
      nodeId: node.id,
      operation,
      filePath,
      inputs,
      data: this.getNodeProperty(node, 'data', '')
    };

    const response = await fetch('/api/nodes/db/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw this.createExecutionError(
        `DB operation API call failed: ${response.status} ${errorText}`,
        node,
        { 
          operation,
          filePath,
          status: response.status,
          error: errorText
        }
      );
    }

    const result = await response.json();
    
    // Return the result from the API
    return result.output || result.data || result;
  }
}