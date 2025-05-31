/**
 * DB executor - handles file I/O and database operations
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/execution';

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
   * Execute database operation - this would be implemented differently in server vs client
   */
  private async executeDBOperation(
    operation: string,
    filePath: string,
    inputs: Record<string, any>,
    node: Node
  ): Promise<any> {
    // This is a client-side executor running in browser environment
    // DB nodes require server-side execution for:
    // 1. File system access
    // 2. Security and path validation
    // 3. Database connections
    // 4. Large file processing
    
    const errorDetails = {
      operation,
      filePath,
      requiredEnvironment: 'server',
      currentEnvironment: 'client',
      suggestion: 'This node will be executed on the server in hybrid execution mode'
    };
    
    switch (operation) {
      case 'read':
        throw this.createExecutionError(
          'File read operations require server-side execution for security and file system access.',
          node,
          errorDetails
        );
      case 'write':
        throw this.createExecutionError(
          'File write operations require server-side execution for security and file system access.',
          node,
          errorDetails
        );
      case 'append':
        throw this.createExecutionError(
          'File append operations require server-side execution for security and file system access.',
          node,
          errorDetails
        );
      case 'delete':
        throw this.createExecutionError(
          'File delete operations require server-side execution for security and file system access.',
          node,
          errorDetails
        );
      case 'list':
        throw this.createExecutionError(
          'Directory listing operations require server-side execution for security and file system access.',
          node,
          errorDetails
        );
      case 'query':
        throw this.createExecutionError(
          'Database query operations require server-side execution for security and database access.',
          node,
          errorDetails
        );
      default:
        throw this.createExecutionError(
          `Unsupported DB operation: ${operation}`,
          node,
          { ...errorDetails, operation }
        );
    }
  }
}