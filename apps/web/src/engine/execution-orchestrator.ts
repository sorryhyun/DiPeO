/**
 * Environment-agnostic execution orchestrator
 * 
 * This module provides a unified interface for diagram execution that works
 * in both client and server environments, demonstrating the Phase 3 goal
 * of environment-agnostic execution logic.
 */

import { 
  Diagram, 
  ExecutionOptions, 
  ExecutionResult,
  ExecutionStatus
} from '@/shared/types/execution';

import { ExecutionEngine } from './core/execution-engine';
import { 
  createExecutorFactory, 
  ExecutorFactory,
  getExecutionCapabilities 
} from './executors';

export interface ExecutionOrchestrator {
  /**
   * Execute a diagram with automatic environment detection
   */
  execute(diagram: Diagram, options?: ExecutionOptions): Promise<ExecutionResult>;
  
  /**
   * Check if a diagram can be executed in the current environment
   */
  canExecute(diagram: Diagram): boolean;
  
  /**
   * Get execution capabilities for the current environment
   */
  getCapabilities(): any;
  
  /**
   * Stop current execution
   */
  stop(): Promise<void>;
}

/**
 * Standard execution orchestrator that works in any environment
 */
export class StandardExecutionOrchestrator implements ExecutionOrchestrator {
  private executionEngine: ExecutionEngine;
  private executorFactory: ExecutorFactory;
  private currentExecution?: Promise<ExecutionResult>;

  constructor(
    environment?: 'client' | 'server',
    streamManager?: any
  ) {
    this.executorFactory = createExecutorFactory(environment);
    this.executionEngine = new ExecutionEngine(this.executorFactory, streamManager);
  }

  async execute(diagram: Diagram, options: ExecutionOptions = {}): Promise<ExecutionResult> {
    // Validate that the diagram can be executed
    if (!this.canExecute(diagram)) {
      const unsupportedNodes = this.getUnsupportedNodes(diagram);
      const result: ExecutionResult = {
        success: false,
        context: {} as any,
        metadata: {
          executionId: '',
          startTime: Date.now(),
          totalCost: 0,
          nodeCount: diagram.nodes.length,
          status: 'failed'
        },
        finalOutputs: {},
        errors: [{
          message: `Cannot execute diagram in ${this.executorFactory.getEnvironment()} environment. Unsupported nodes: ${unsupportedNodes.join(', ')}`,
          timestamp: new Date(),
          details: { unsupportedNodes, environment: this.executorFactory.getEnvironment() }
        }]
      };
      return result;
    }

    // Execute the diagram
    this.currentExecution = this.executionEngine.execute(diagram, options);
    return this.currentExecution;
  }

  canExecute(diagram: Diagram): boolean {
    const nodeTypes = diagram.nodes.map(node => node.type);
    return nodeTypes.every(nodeType => this.executorFactory.canExecute(nodeType));
  }

  getCapabilities() {
    return getExecutionCapabilities(this.executorFactory.getEnvironment());
  }

  async stop(): Promise<void> {
    if (this.currentExecution) {
      await this.executionEngine.stop();
    }
  }

  /**
   * Get unsupported node types for the current environment
   */
  private getUnsupportedNodes(diagram: Diagram): string[] {
    return diagram.nodes
      .map(node => node.type)
      .filter(nodeType => !this.executorFactory.canExecute(nodeType));
  }

  /**
   * Get the execution environment
   */
  getEnvironment(): 'client' | 'server' {
    return this.executorFactory.getEnvironment();
  }

  /**
   * Create an execution plan for the diagram
   */
  createExecutionPlan(diagram: Diagram): {
    canExecute: boolean;
    environment: 'client' | 'server';
    supportedNodes: string[];
    unsupportedNodes: string[];
    executionStrategy: string;
  } {
    const nodeTypes = diagram.nodes.map(node => node.type);
    const supportedNodes = nodeTypes.filter(type => this.executorFactory.canExecute(type));
    const unsupportedNodes = nodeTypes.filter(type => !this.executorFactory.canExecute(type));
    
    return {
      canExecute: unsupportedNodes.length === 0,
      environment: this.executorFactory.getEnvironment(),
      supportedNodes,
      unsupportedNodes,
      executionStrategy: this.determineExecutionStrategy(nodeTypes)
    };
  }

  private determineExecutionStrategy(nodeTypes: string[]): string {
    const capabilities = this.getCapabilities();
    const hasClientSafe = nodeTypes.some(type => capabilities.clientSafe.includes(type));
    const hasServerOnly = nodeTypes.some(type => capabilities.serverOnly.includes(type));
    
    if (hasServerOnly && hasClientSafe) {
      return 'hybrid';
    } else if (hasServerOnly) {
      return 'server-only';
    } else {
      return 'client-only';
    }
  }
}

/**
 * Hybrid execution orchestrator that can route execution between client and server
 * This represents the future Phase 6 implementation
 */
export class HybridExecutionOrchestrator implements ExecutionOrchestrator {
  private clientOrchestrator: StandardExecutionOrchestrator;
  private serverOrchestrator?: StandardExecutionOrchestrator;

  constructor(streamManager?: any) {
    this.clientOrchestrator = new StandardExecutionOrchestrator('client', streamManager);
    // Server orchestrator would be initialized differently in a real implementation
  }

  async execute(diagram: Diagram, options: ExecutionOptions = {}): Promise<ExecutionResult> {
    const executionPlan = this.createHybridExecutionPlan(diagram);
    
    switch (executionPlan.strategy) {
      case 'client-only':
        return this.clientOrchestrator.execute(diagram, options);
      
      case 'server-only':
        if (!this.serverOrchestrator) {
          throw new Error('Server orchestrator not available for server-only execution');
        }
        return this.serverOrchestrator.execute(diagram, options);
      
      case 'hybrid':
        return this.executeHybrid(diagram, options, executionPlan);
      
      default:
        throw new Error(`Unknown execution strategy: ${executionPlan.strategy}`);
    }
  }

  canExecute(diagram: Diagram): boolean {
    // Hybrid orchestrator can execute any diagram by routing appropriately
    const plan = this.createHybridExecutionPlan(diagram);
    return plan.strategy !== 'unsupported';
  }

  getCapabilities() {
    return {
      client: this.clientOrchestrator.getCapabilities(),
      server: this.serverOrchestrator?.getCapabilities(),
      hybrid: true
    };
  }

  async stop(): Promise<void> {
    await Promise.all([
      this.clientOrchestrator.stop(),
      this.serverOrchestrator?.stop()
    ]);
  }

  /**
   * Create a hybrid execution plan
   */
  private createHybridExecutionPlan(diagram: Diagram): {
    strategy: 'client-only' | 'server-only' | 'hybrid' | 'unsupported';
    clientNodes: string[];
    serverNodes: string[];
    unsupportedNodes: string[];
  } {
    const clientCapabilities = this.clientOrchestrator.getCapabilities();
    const nodeTypes = diagram.nodes.map(node => node.type);
    
    const clientNodes = nodeTypes.filter(type => clientCapabilities.clientSafe.includes(type));
    const serverNodes = nodeTypes.filter(type => clientCapabilities.serverOnly.includes(type));
    const unsupportedNodes = nodeTypes.filter(type => 
      !clientCapabilities.clientSafe.includes(type) && 
      !clientCapabilities.serverOnly.includes(type)
    );

    let strategy: 'client-only' | 'server-only' | 'hybrid' | 'unsupported';
    
    if (unsupportedNodes.length > 0) {
      strategy = 'unsupported';
    } else if (serverNodes.length === 0) {
      strategy = 'client-only';
    } else if (clientNodes.length === 0) {
      strategy = 'server-only';
    } else {
      strategy = 'hybrid';
    }

    return {
      strategy,
      clientNodes,
      serverNodes,
      unsupportedNodes
    };
  }

  /**
   * Execute a diagram using hybrid client/server strategy
   * This is a placeholder for Phase 6 implementation
   */
  private async executeHybrid(
    diagram: Diagram, 
    options: ExecutionOptions,
    plan: any
  ): Promise<ExecutionResult> {
    // This would involve:
    // 1. Partitioning the diagram into client and server sub-graphs
    // 2. Executing client-safe nodes locally
    // 3. Sending server-only nodes to server for execution
    // 4. Coordinating data flow between client and server
    // 5. Merging results into a unified execution result
    
    throw new Error('Hybrid execution not yet implemented (Phase 6)');
  }
}

/**
 * Factory function to create the appropriate orchestrator
 */
export function createExecutionOrchestrator(
  type: 'standard' | 'hybrid' = 'standard',
  environment?: 'client' | 'server',
  streamManager?: any
): ExecutionOrchestrator {
  switch (type) {
    case 'standard':
      return new StandardExecutionOrchestrator(environment, streamManager);
    case 'hybrid':
      return new HybridExecutionOrchestrator(streamManager);
    default:
      throw new Error(`Unknown orchestrator type: ${type}`);
  }
}

/**
 * Convenience function for simple diagram execution
 */
export async function executeDiagram(
  diagram: Diagram,
  options: ExecutionOptions = {},
  environment?: 'client' | 'server'
): Promise<ExecutionResult> {
  const orchestrator = createExecutionOrchestrator('standard', environment);
  return orchestrator.execute(diagram, options);
}

/**
 * Check execution compatibility for a diagram
 */
export function checkExecutionCompatibility(
  diagram: Diagram,
  environment?: 'client' | 'server'
): {
  canExecute: boolean;
  plan: any;
  recommendations: string[];
} {
  const orchestrator = createExecutionOrchestrator('standard', environment);
  const plan = (orchestrator as StandardExecutionOrchestrator).createExecutionPlan(diagram);
  
  const recommendations: string[] = [];
  
  if (!plan.canExecute) {
    if (plan.environment === 'client' && plan.unsupportedNodes.length > 0) {
      recommendations.push('Consider executing on server for full functionality');
      recommendations.push(`Unsupported client nodes: ${plan.unsupportedNodes.join(', ')}`);
    } else {
      recommendations.push('Some node types are not supported in any environment');
    }
  }
  
  if (plan.executionStrategy === 'hybrid') {
    recommendations.push('Consider using hybrid execution for optimal performance');
  }

  return {
    canExecute: plan.canExecute,
    plan,
    recommendations
  };
}