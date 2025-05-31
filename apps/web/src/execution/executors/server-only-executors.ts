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
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
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

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    const personId = this.getNodeProperty(node, 'personId', '');
    const prompt = this.getNodeProperty(node, 'prompt', '');
    const llmService = this.getNodeProperty(node, 'llmService', '') as LLMService;
    const inputs = this.getInputValues(node, context);
    
    try {
      // This would be implemented by the server-side version
      const result = await this.executeLLMCall(personId, prompt, llmService, inputs, node, context);
      
      return this.createSuccessResult(result.text, result.cost || 0, {
        personId,
        llmService,
        usage: result.usage,
        promptTokens: result.promptTokens,
        completionTokens: result.completionTokens,
        totalTokens: result.totalTokens,
        executedAt: new Date().toISOString()
      });
    } catch (error) {
      throw this.createExecutionError(
        `Failed to execute PersonJob: ${error.message}`,
        node,
        { personId, llmService, error: error.message }
      );
    }
  }

  /**
   * Execute LLM call - this would be implemented differently in server vs client
   */
  private async executeLLMCall(
    personId: string,
    prompt: string,
    llmService: LLMService,
    inputs: Record<string, any>,
    node: Node,
    context: TypedExecutionContext
  ): Promise<ChatResult> {
    // In a real implementation, this would:
    // 1. Load person context and memory
    // 2. Construct the full prompt with inputs and context
    // 3. Make the API call to the specified LLM service
    // 4. Update person memory with the conversation
    // 5. Track costs and usage
    
    throw new Error('PersonJob execution must be implemented by server-side executor factory');
  }
}

/**
 * PersonBatchJob executor - handles batch LLM processing
 */
export class PersonBatchJobExecutor extends ServerOnlyExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
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
    if (typeof batchSize !== 'number' || batchSize < 1) {
      errors.push('Batch size must be a positive number');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
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
        `Failed to execute PersonBatchJob: ${error.message}`,
        node,
        { personId, llmService, batchSize, error: error.message }
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
    // In a real implementation, this would:
    // 1. Extract batch data from inputs
    // 2. Split into batches of specified size
    // 3. Execute LLM calls for each batch item
    // 4. Aggregate results and costs
    // 5. Update person memory appropriately
    
    throw new Error('PersonBatchJob execution must be implemented by server-side executor factory');
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
    const operation = this.getNodeProperty(node, 'operation', '');
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
        `Failed to execute DB operation: ${error.message}`,
        node,
        { operation, filePath, error: error.message }
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
    // In a real implementation, this would:
    // 1. Validate file paths and permissions
    // 2. Handle different file formats (JSON, CSV, txt, etc.)
    // 3. Perform the requested operation
    // 4. Return appropriate results
    
    switch (operation) {
      case 'read':
        throw new Error('File read operation must be implemented by server-side executor factory');
      case 'write':
        throw new Error('File write operation must be implemented by server-side executor factory');
      case 'append':
        throw new Error('File append operation must be implemented by server-side executor factory');
      case 'delete':
        throw new Error('File delete operation must be implemented by server-side executor factory');
      case 'list':
        throw new Error('Directory list operation must be implemented by server-side executor factory');
      case 'query':
        throw new Error('Database query operation must be implemented by server-side executor factory');
      default:
        throw new Error(`Unsupported DB operation: ${operation}`);
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