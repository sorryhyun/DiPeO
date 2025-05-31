/**
 * Server-side executor factory that creates executors for Node.js environment
 * Supports both client-safe and server-only operations
 */

import { BaseExecutorInterface } from '@/shared/types/execution';
import { 
  BaseExecutorFactory, 
  ExecutorNotFoundError 
} from './base-executor';

import {
  StartExecutor,
  ConditionExecutor,
  JobExecutor,
  EndpointExecutor
} from './client-safe-executors';

import {
  PersonJobExecutor,
  PersonBatchJobExecutor,
  DBExecutor
} from './server-only-executors';

export class ServerExecutorFactory extends BaseExecutorFactory {
  constructor() {
    super();
    this.registerAllExecutors();
  }

  getEnvironment(): 'client' | 'server' {
    return 'server';
  }

  createExecutor(nodeType: string): BaseExecutorInterface {
    const executorFactory = this.executors.get(nodeType);
    
    if (executorFactory) {
      return executorFactory();
    }

    throw new ExecutorNotFoundError(nodeType, this.getEnvironment());
  }

  canExecute(nodeType: string): boolean {
    // Server can execute all supported node types
    return this.executors.has(nodeType);
  }

  /**
   * Register all executors (client-safe and server-only)
   */
  private registerAllExecutors(): void {
    // Client-safe executors
    this.registerClientSafeExecutors();
    
    // Server-only executors
    this.registerServerOnlyExecutors();
  }

  /**
   * Register client-safe executors
   */
  private registerClientSafeExecutors(): void {
    // Start node
    this.registerExecutor('start', () => new StartExecutor());
    this.registerExecutor('startNode', () => new StartExecutor());

    // Condition node
    this.registerExecutor('condition', () => new ConditionExecutor());
    this.registerExecutor('conditionNode', () => new ConditionExecutor());

    // Job node
    this.registerExecutor('job', () => new JobExecutor());
    this.registerExecutor('jobNode', () => new JobExecutor());

    // Endpoint node
    this.registerExecutor('endpoint', () => new EndpointExecutor());
    this.registerExecutor('endpointNode', () => new EndpointExecutor());
  }

  /**
   * Register server-only executors
   */
  private registerServerOnlyExecutors(): void {
    // PersonJob node
    this.registerExecutor('person_job', () => new PersonJobExecutor());
    this.registerExecutor('personJobNode', () => new PersonJobExecutor());

    // PersonBatchJob node
    this.registerExecutor('person_batch_job', () => new PersonBatchJobExecutor());
    this.registerExecutor('personBatchJobNode', () => new PersonBatchJobExecutor());

    // DB node
    this.registerExecutor('db', () => new DBExecutor());
    this.registerExecutor('dbNode', () => new DBExecutor());
  }

  /**
   * Get information about execution capabilities
   */
  getExecutionCapabilities(): {
    clientSafe: string[];
    serverOnly: string[];
    supported: string[];
  } {
    return {
      clientSafe: [
        'start',
        'startNode',
        'condition', 
        'conditionNode',
        'job',
        'jobNode', 
        'endpoint',
        'endpointNode'
      ],
      serverOnly: [
        'person_job',
        'personJobNode',
        'person_batch_job', 
        'personBatchJobNode',
        'db',
        'dbNode'
      ],
      supported: this.getSupportedNodeTypes()
    };
  }

  /**
   * Check if a diagram can be fully executed in server environment
   */
  canExecuteDiagram(nodeTypes: string[]): {
    canExecute: boolean;
    unsupportedNodes: string[];
  } {
    const unsupportedNodes: string[] = [];

    for (const nodeType of nodeTypes) {
      if (!this.canExecute(nodeType)) {
        unsupportedNodes.push(nodeType);
      }
    }

    return {
      canExecute: unsupportedNodes.length === 0,
      unsupportedNodes
    };
  }

  /**
   * Check if a node type is client-safe
   */
  isClientSafeNodeType(nodeType: string): boolean {
    const clientSafeTypes = [
      'start',
      'startNode',
      'condition', 
      'conditionNode',
      'job',
      'jobNode', 
      'endpoint',
      'endpointNode'
    ];
    return clientSafeTypes.includes(nodeType);
  }

  /**
   * Check if a node type requires server-side execution
   */
  isServerOnlyNodeType(nodeType: string): boolean {
    const serverOnlyTypes = [
      'person_job',
      'personJobNode',
      'person_batch_job', 
      'personBatchJobNode',
      'db',
      'dbNode'
    ];
    return serverOnlyTypes.includes(nodeType);
  }

  /**
   * Create execution plan with environment routing information
   */
  createExecutionPlan(nodeTypes: string[]): {
    clientNodes: string[];
    serverNodes: string[];
    unsupportedNodes: string[];
    executionStrategy: 'client-only' | 'server-only' | 'hybrid';
  } {
    const clientNodes: string[] = [];
    const serverNodes: string[] = [];
    const unsupportedNodes: string[] = [];

    for (const nodeType of nodeTypes) {
      if (this.isClientSafeNodeType(nodeType)) {
        clientNodes.push(nodeType);
      } else if (this.isServerOnlyNodeType(nodeType)) {
        serverNodes.push(nodeType);
      } else {
        unsupportedNodes.push(nodeType);
      }
    }

    let executionStrategy: 'client-only' | 'server-only' | 'hybrid';
    if (serverNodes.length === 0) {
      executionStrategy = 'client-only';
    } else if (clientNodes.length === 0) {
      executionStrategy = 'server-only';
    } else {
      executionStrategy = 'hybrid';
    }

    return {
      clientNodes,
      serverNodes,
      unsupportedNodes,
      executionStrategy
    };
  }
}