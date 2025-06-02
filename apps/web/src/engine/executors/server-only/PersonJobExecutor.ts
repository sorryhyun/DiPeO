/**
 * PersonJob executor - handles LLM API calls with context and memory
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext,
  ChatResult
} from '@/shared/types/core';

import { ServerOnlyExecutor } from '../base-executor';
import { getApiUrl } from '@/shared/utils/apiConfig';

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

    // Validate prompt - must have either defaultPrompt or firstOnlyPrompt
    const defaultPrompt = this.getNodeProperty(node, 'defaultPrompt', '');
    const firstOnlyPrompt = this.getNodeProperty(node, 'firstOnlyPrompt', '');
    if (!defaultPrompt && !firstOnlyPrompt) {
      errors.push('Either defaultPrompt or firstOnlyPrompt is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  async execute(node: Node, context: TypedExecutionContext, _options?: any): Promise<ExecutorResult> {
    const personId = this.getNodeProperty(node, 'personId', '');
    const inputs = this.getInputValues(node, context);
    
    try {
      // This would be implemented by the server-side version
      const result = await this.executeLLMCall(personId, inputs, node, context);
      
      // Calculate cost from the backend response
      const cost = result.usage?.cost || 0;
      
      return this.createSuccessResult(result.text, cost, {
        personId,
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
        { personId, error: errorMessage }
      );
    }
  }

  /**
   * Execute LLM call via backend API
   */
  private async executeLLMCall(
    personId: string,
    inputs: Record<string, any>,
    node: Node,
    context: TypedExecutionContext
  ): Promise<ChatResult> {
    // Get the full person configuration from the store
    // Import at the top level would cause circular dependency, so we import here
    const { useConsolidatedDiagramStore } = await import('@/core/stores');
    const getPersonById = useConsolidatedDiagramStore.getState().getPersonById;
    const person = getPersonById(personId);
    
    console.log('[PersonJobExecutor] Retrieving person configuration:', {
      personId,
      personFound: !!person,
      personData: person,
      allPersons: useConsolidatedDiagramStore.getState().persons
    });
    
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

    console.log('[PersonJobExecutor] Sending payload to backend:', {
      nodeId: node.id,
      personId: person.id,
      personService: person.service,
      personModel: person.modelName,
      personApiKeyId: person.apiKeyId,
      hasSystemPrompt: !!person.systemPrompt,
      promptLength: promptToUse.length,
      inputKeys: Object.keys(inputs)
    });

    const response = await fetch(getApiUrl('/api/nodes/personjob/execute'), {
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