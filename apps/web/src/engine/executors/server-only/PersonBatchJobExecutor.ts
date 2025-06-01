/**
 * PersonBatchJob executor - handles batch LLM processing
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext,
  LLMService,
  ChatResult
} from '@/shared/types/core';

import { ServerOnlyExecutor } from '../base-executor';

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