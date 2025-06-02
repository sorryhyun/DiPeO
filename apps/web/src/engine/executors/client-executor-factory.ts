/**
 * Client-side executor factory that creates executors for browser environment
 * Only supports client-safe operations
 */

import { BaseExecutorInterface } from '@/shared/types/core';
import { 
  BaseExecutorFactory, 
  ExecutorNotFoundError, 
  UnsupportedEnvironmentError 
} from './base-executor';

import {
  StartExecutor,
  ConditionExecutor,
  JobExecutor,
  EndpointExecutor
} from './client-safe-executors';

import { UnsupportedServerExecutor } from './server-only-executors';

export class ClientExecutorFactory extends BaseExecutorFactory {
  constructor() {
    super();
    this.registerClientSafeExecutors();
  }

  getEnvironment(): 'client' | 'server' {
    return 'client';
  }

  createExecutor(nodeType: string): BaseExecutorInterface {
    const executorFactory = this.executors.get(nodeType);
    
    if (executorFactory) {
      return executorFactory();
    }

    // Check if this is a server-only node type
    if (this.isServerOnlyNodeType(nodeType)) {
      return new UnsupportedServerExecutor(nodeType);
    }

    throw new ExecutorNotFoundError(nodeType, this.getEnvironment());
  }

  canExecute(nodeType: string): boolean {
    // Client can only execute client-safe node types
    return this.isClientSafeNodeType(nodeType);
  }

  /**
   * Register all client-safe executors
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
   * Check if a node type is client-safe
   */
  private isClientSafeNodeType(nodeType: string): boolean {
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
   * Get information about what can and cannot be executed in client environment
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
   * Check if a diagram can be fully executed in client environment
   */
  canExecuteDiagram(nodeTypes: string[]): {
    canExecute: boolean;
    unsupportedNodes: string[];
    serverOnlyNodes: string[];
  } {
    const unsupportedNodes: string[] = [];
    const serverOnlyNodes: string[] = [];

    for (const nodeType of nodeTypes) {
      if (this.isServerOnlyNodeType(nodeType)) {
        serverOnlyNodes.push(nodeType);
      } else if (!this.isClientSafeNodeType(nodeType)) {
        unsupportedNodes.push(nodeType);
      }
    }

    return {
      canExecute: unsupportedNodes.length === 0 && serverOnlyNodes.length === 0,
      unsupportedNodes,
      serverOnlyNodes
    };
  }

  /**
   * Create a hybrid execution plan that identifies which nodes need server execution
   */
  createHybridExecutionPlan(nodeTypes: string[]): {
    clientNodes: string[];
    serverNodes: string[];
    unsupportedNodes: string[];
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

    return {
      clientNodes,
      serverNodes,
      unsupportedNodes
    };
  }
}