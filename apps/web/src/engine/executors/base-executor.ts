/**
 * Base executor interface and abstract implementations
 */

import { 
  Node, 
  ExecutorResult, 
  ExecutorValidation, 
  BaseExecutorInterface,
  ExecutionContext as TypedExecutionContext,
  NodeExecutionError
} from '@/shared/types/core';

/**
 * Abstract base executor that provides common functionality
 */
export abstract class BaseExecutor implements BaseExecutorInterface {
  abstract validateInputs(node: Node, context: TypedExecutionContext): Promise<ExecutorValidation>;
  abstract execute(node: Node, context: TypedExecutionContext, options?: any): Promise<ExecutorResult>;

  /**
   * Validate common node properties
   */
  protected validateCommonInputs(node: Node): ExecutorValidation {
    const errors: string[] = [];

    if (!node.id) {
      errors.push('Node ID is required');
    }

    if (!node.type) {
      errors.push('Node type is required');
    }

    if (!node.data) {
      errors.push('Node data is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get input values from connected arrows
   */
  protected getInputValues(node: Node, context: TypedExecutionContext): Record<string, any> {
    const inputs: Record<string, any> = {};
    const incomingArrows = context.incomingArrows[node.id] || [];

    for (const arrow of incomingArrows) {
      if (arrow.source && context.nodeOutputs[arrow.source] !== undefined) {
        // Use target handle as input key, fallback to source handle or source node ID
        const inputKey = arrow.targetHandle || arrow.sourceHandle || arrow.source;
        inputs[inputKey] = context.nodeOutputs[arrow.source];
      }
    }

    return inputs;
  }

  /**
   * Create a successful execution result
   */
  protected createSuccessResult(output: any, cost: number = 0, metadata?: Record<string, any>): ExecutorResult {
    return {
      output,
      cost,
      metadata: metadata || {}
    };
  }

  /**
   * Create an execution error
   */
  protected createExecutionError(message: string, node: Node, details?: Record<string, any>): NodeExecutionError {
    return new NodeExecutionError(message, node.id, node.type, details);
  }

  /**
   * Get a property from node data with optional default value
   */
  protected getNodeProperty<T>(node: Node, propertyName: string, defaultValue?: T): T {
    return node.data[propertyName] ?? defaultValue;
  }

  /**
   * Validate that a required property exists in node data
   */
  protected validateRequiredProperty(node: Node, propertyName: string): string | null {
    const value = node.data[propertyName];
    if (value === undefined || value === null || value === '') {
      return `Property '${propertyName}' is required`;
    }
    return null;
  }

  /**
   * Get execution count for this specific node
   */
  protected getExecutionCount(node: Node, context: TypedExecutionContext): number {
    return context.nodeExecutionCounts[node.id] || 0;
  }

  /**
   * Check if this is the first execution of the node
   */
  protected isFirstExecution(node: Node, context: TypedExecutionContext): boolean {
    return this.getExecutionCount(node, context) === 0;
  }
}

/**
 * Client-safe base executor for nodes that can run in browser
 */
export abstract class ClientSafeExecutor extends BaseExecutor {
  /**
   * Client-safe executors should not make external API calls
   */
  protected validateNoExternalAPICalls(): ExecutorValidation {
    // This is a compile-time reminder that client-safe executors 
    // should not make external API calls
    return { isValid: true, errors: [] };
  }
}

/**
 * Server-only base executor for nodes that require server-side execution
 */
export abstract class ServerOnlyExecutor extends BaseExecutor {
  /**
   * Server-only executors can make external API calls and access sensitive data
   */
  protected canMakeExternalAPICalls(): boolean {
    return true;
  }

  /**
   * Check if API keys are available (placeholder for server-side implementation)
   */
  protected hasAPIKeys(): boolean {
    // This would be implemented differently in server vs client environments
    return false;
  }
}

/**
 * Factory interface for creating executors
 */
export interface ExecutorFactory {
  /**
   * Create an executor for a specific node type
   */
  createExecutor(nodeType: string): BaseExecutorInterface;
  
  /**
   * Check if a node type can be executed in the current environment
   */
  canExecute(nodeType: string): boolean;
  
  /**
   * Get all supported node types in this environment
   */
  getSupportedNodeTypes(): string[];
  
  /**
   * Get execution environment (client or server)
   */
  getEnvironment(): 'client' | 'server';
}

/**
 * Base factory implementation with common functionality
 */
export abstract class BaseExecutorFactory implements ExecutorFactory {
  protected executors: Map<string, () => BaseExecutorInterface> = new Map();

  abstract createExecutor(nodeType: string): BaseExecutorInterface;
  abstract getEnvironment(): 'client' | 'server';

  canExecute(nodeType: string): boolean {
    return this.executors.has(nodeType);
  }

  getSupportedNodeTypes(): string[] {
    return Array.from(this.executors.keys());
  }

  /**
   * Register an executor for a node type
   */
  protected registerExecutor(nodeType: string, executorFactory: () => BaseExecutorInterface): void {
    this.executors.set(nodeType, executorFactory);
  }
}

/**
 * Error types for executor operations
 */
export class ExecutorNotFoundError extends Error {
  constructor(nodeType: string, environment: string) {
    super(`No executor found for node type '${nodeType}' in ${environment} environment`);
    this.name = 'ExecutorNotFoundError';
  }
}

export class UnsupportedEnvironmentError extends Error {
  constructor(nodeType: string, requiredEnvironment: string, currentEnvironment: string) {
    super(
      `Node type '${nodeType}' requires ${requiredEnvironment} environment but current environment is ${currentEnvironment}`
    );
    this.name = 'UnsupportedEnvironmentError';
  }
}