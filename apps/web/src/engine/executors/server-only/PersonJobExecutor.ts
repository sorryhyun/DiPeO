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
    const llmService = this.getNodeProperty(node, 'llmService', '') as LLMService;
    const inputs = this.getInputValues(node, context);
    
    try {
      // This would be implemented by the server-side version
      const result = await this.executeLLMCall(personId, llmService, inputs, node, context);
      
      // Calculate cost from the backend response
      const cost = result.usage?.cost || 0;
      
      return this.createSuccessResult(result.text, cost, {
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
   * Execute LLM call via backend API
   */
  private async executeLLMCall(
    personId: string,
    llmService: LLMService,
    inputs: Record<string, any>,
    node: Node,
    context: TypedExecutionContext
  ): Promise<ChatResult> {
    // Get the full person configuration from the store
    // Import at the top level would cause circular dependency, so we import here
    const { useConsolidatedDiagramStore } = await import('@/core/stores');
    const getPersonById = useConsolidatedDiagramStore.getState().getPersonById;
    const person = getPersonById(personId);
    
    if (!person) {
      throw this.createExecutionError(
        `Person with ID ${personId} not found`,
        node,
        { personId }
      );
    }

    // Get the actual prompt to use based on execution count and available prompts
    const executionCount = context.nodeExecutionCounts[node.id] || 0;
    const isFirstExecution = executionCount === 0;
    const firstOnlyPrompt = this.getNodeProperty(node, 'firstOnlyPrompt', '');
    const defaultPrompt = this.getNodeProperty(node, 'defaultPrompt', '');
    
    // Use firstOnlyPrompt for first execution if available, otherwise use defaultPrompt
    const promptToUse = isFirstExecution && firstOnlyPrompt ? firstOnlyPrompt : defaultPrompt;
    
    // Call backend API for PersonJob execution
    const payload = {
      nodeId: node.id,
      person: person, // Send full person configuration
      prompt: promptToUse, // Use the appropriate prompt
      inputs,
      node_config: {
        iterationCount: this.getNodeProperty(node, 'iterationCount', 1),
        contextCleaningRule: this.getNodeProperty(node, 'contextCleaningRule', 'uponRequest')
      }
    };

    const response = await fetch('/api/nodes/personjob/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw this.createExecutionError(
        `PersonJob API call failed: ${response.status} ${errorText}`,
        node,
        { 
          personId, 
          llmService,
          status: response.status,
          error: errorText
        }
      );
    }

    const result = await response.json();
    
    // Return standardized ChatResult
    return {
      text: result.output || result.text || '',
      usage: result.usage || { cost: result.cost || 0 },
      promptTokens: result.promptTokens || result.prompt_tokens || 0,
      completionTokens: result.completionTokens || result.completion_tokens || 0,
      totalTokens: result.totalTokens || result.total_tokens || 0
    };
  }
}