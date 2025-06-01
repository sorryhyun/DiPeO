/**
 * Placeholder executor for unsupported server-only operations in client environment
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation,
  ExecutionContext as TypedExecutionContext
} from '@/shared/types/core';

import { ServerOnlyExecutor } from '../base-executor';

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