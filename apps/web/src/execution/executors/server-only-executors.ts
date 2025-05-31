/**
 * Server-only executors that require server-side execution
 * These executors handle external API calls, file operations, and sensitive data
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext,
  LLMService,
  ChatResult
} from '@/shared/types/execution';

import { ServerOnlyExecutor } from './base-executor';

/**
 * PersonJob executor - handles LLM API calls with context and memory
 */
export class PersonJobExecutor extends ServerOnlyExecutor {
  async validateInputs(node: Node, _context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Validate person ID
    const personId = this.getNodeProperty(node, 'personId', '');
    if (!personId) {
      errors.push('Person ID is required');
    }

    // Validate prompt
    const prompt = this.getNodeProperty(node, 'prompt', '');
    if (!prompt) {
      errors.push('Prompt is required');
    }

    // Validate LLM service
    const llmService = this.getNodeProperty(node, 'llmService', '');
    if (!llmService) {
      errors.push('LLM service is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, _options?: any): Promise<ExecutorResult> {
    const personId = this.getNodeProperty(node, 'personId', '');
    const prompt = this.getNodeProperty(node, 'prompt', '');
    const llmService = this.getNodeProperty(node, 'llmService', '') as LLMService;
    const inputs = this.getInputValues(node, context);
    
    try {
      // This would be implemented by the server-side version
      const result = await this.executeLLMCall(personId, prompt, llmService, inputs, node, context);
      
      return this.createSuccessResult(result.text, 0, {
        personId,
        llmService,
        usage: result.usage,
        promptTokens: result.promptTokens,
        completionTokens: result.completionTokens,
        totalTokens: result.totalTokens,
        executedAt: new Date().toISOString()
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw this.createExecutionError(
        `Failed to execute PersonJob: ${errorMessage}`,
        node,
        { personId, llmService, error: errorMessage }
      );
    }
  }

  /**
   * Execute LLM call - this would be implemented differently in server vs client
   */
  private async executeLLMCall(
    personId: string,
    _prompt: string,
    llmService: LLMService,
    _inputs: Record<string, any>,
    node: Node,
    _context: TypedExecutionContext
  ): Promise<ChatResult> {
    // This is a client-side executor running in browser environment
    // PersonJob nodes require server-side execution for:
    // 1. Secure API key access
    // 2. LLM API calls
    // 3. Memory management
    // 4. Cost tracking
    
    throw this.createExecutionError(
      'PersonJob nodes require server-side execution. Use hybrid execution mode or run diagram on server.',
      node,
      { 
        personId, 
        llmService,
        requiredEnvironment: 'server',
        currentEnvironment: 'client',
        suggestion: 'This node will be executed on the server in hybrid execution mode'
      }
    );
  }
}

/**
 * PersonBatchJob executor - handles batch LLM processing
 */
export class PersonBatchJobExecutor extends ServerOnlyExecutor {
  async validateInputs(node: Node, _context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    const errors: string[] = [];

    // Validate person ID
    const personId = this.getNodeProperty(node, 'personId', '');
    if (!personId) {
      errors.push('Person ID is required');
    }

    // Validate batch prompt
    const batchPrompt = this.getNodeProperty(node, 'batchPrompt', '');
    if (!batchPrompt) {
      errors.push('Batch prompt is required');
    }

    // Validate LLM service
    const llmService = this.getNodeProperty(node, 'llmService', '');
    if (!llmService) {
      errors.push('LLM service is required');
    }

    // Validate batch size
    const batchSize = this.getNodeProperty(node, 'batchSize', 10);
    if (batchSize < 1) {
      errors.push('Batch size must be a positive number');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, _options?: Record<string, unknown>): Promise<ExecutorResult> {
    const personId = this.getNodeProperty(node, 'personId', '');
    const batchPrompt = this.getNodeProperty(node, 'batchPrompt', '');
    const llmService = this.getNodeProperty(node, 'llmService', '') as LLMService;
    const batchSize = this.getNodeProperty(node, 'batchSize', 10);
    const inputs = this.getInputValues(node, context);
    
    try {
      // This would be implemented by the server-side version
      const results = await this.executeBatchLLMCall(
        personId, 
        batchPrompt, 
        llmService, 
        batchSize, 
        inputs, 
        node, 
        context
      );
      
      const totalCost = results.reduce((sum, result) => sum + (result.cost || 0), 0);
      const allResponses = results.map(result => result.text);
      
      return this.createSuccessResult(allResponses, totalCost, {
        personId,
        llmService,
        batchSize,
        resultCount: results.length,
        totalCost,
        executedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to execute PersonBatchJob: ${error instanceof Error ? error.message : String(error)}`,
        node,
        { personId, llmService, batchSize, error: error instanceof Error ? error.message : String(error) }
      );
    }
  }

  /**
   * Execute batch LLM calls - this would be implemented differently in server vs client
   */
  private async executeBatchLLMCall(
    personId: string,
    batchPrompt: string,
    llmService: LLMService,
    batchSize: number,
    inputs: Record<string, any>,
    node: Node,
    context: TypedExecutionContext
  ): Promise<Array<ChatResult & { cost?: number }>> {
    // This is a client-side executor running in browser environment
    // PersonBatchJob nodes require server-side execution for:
    // 1. Secure API key access
    // 2. Batch LLM API calls
    // 3. Memory management across batch items
    // 4. Cost tracking and rate limiting
    
    throw this.createExecutionError(
      'PersonBatchJob nodes require server-side execution. Use hybrid execution mode or run diagram on server.',
      node,
      { 
        personId, 
        llmService,
        batchSize,
        requiredEnvironment: 'server',
        currentEnvironment: 'client',
        suggestion: 'This node will be executed on the server in hybrid execution mode'
      }
    );
  }
}

/**
 * DB executor - handles file I/O and database operations
 */
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

/**
 * Placeholder executor for unsupported server-only operations in client environment
 */
export class UnsupportedServerExecutor extends ServerOnlyExecutor {
  constructor(private nodeType: string) {
    super();
  }

  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    return {
      isValid: false,
      errors: [`Node type '${this.nodeType}' requires server-side execution`]
    };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    throw this.createExecutionError(
      `Node type '${this.nodeType}' cannot be executed in client environment`,
      node,
      { requiredEnvironment: 'server', currentEnvironment: 'client' }
    );
  }
}