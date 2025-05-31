/**
 * Start node executor - initializes execution flow
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/execution';

import { ClientSafeExecutor } from '../base-executor';

export class StartExecutor extends ClientSafeExecutor {
  async validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation> {
    const commonValidation = this.validateCommonInputs(node);
    if (!commonValidation.isValid) {
      return commonValidation;
    }

    // Start nodes should not have incoming connections
    const incomingArrows = context.incomingArrows[node.id] || [];
    if (incomingArrows.length > 0) {
      return {
        isValid: false,
        errors: ['Start nodes should not have incoming connections']
      };
    }

    return { isValid: true, errors: [] };
  }

  async execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult> {
    // Start nodes can have initial data
    const initialData = this.getNodeProperty(node, 'initialData', {});
    
    return this.createSuccessResult(initialData, 0, {
      executionTime: Date.now() - context.startTime,
      isStartNode: true
    });
  }
}