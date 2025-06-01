/**
 * PersonJob executor - handles LLM API calls with context and memory
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