/**
 * Browser-specific execution orchestrator that avoids server-only imports
 * This provides a safe way to execute diagrams in the browser without Node.js dependencies
 */

import { 
  Diagram, 
  ExecutionOptions, 
  ExecutionResult
} from '@/shared/types/core';
import { createStoreIntegratedStreamManager } from './stream-manager';
import { ClientExecutorFactory } from './executors/client-executor-factory';
import { ExecutionEngine } from './core/execution-engine';

export interface BrowserExecutionOrchestrator {
  execute(diagram: Diagram, options?: ExecutionOptions): Promise<ExecutionResult>;
  canExecute(diagram: Diagram): boolean;
  stop(): Promise<void>;
}

export class StandardBrowserOrchestrator implements BrowserExecutionOrchestrator {
  private executionEngine: ExecutionEngine;
  private executorFactory: ClientExecutorFactory;
  private currentExecution?: Promise<ExecutionResult>;

  constructor() {
    this.executorFactory = new ClientExecutorFactory();
    const streamManager = createStoreIntegratedStreamManager();
    this.executionEngine = new ExecutionEngine(this.executorFactory, streamManager);
  }

  async execute(diagram: Diagram, options: ExecutionOptions = {}): Promise<ExecutionResult> {
    // Check if all nodes can be executed in client environment
    if (!this.canExecute(diagram)) {
      const unsupportedNodes = this.getUnsupportedNodes(diagram);
      
      // For unsupported nodes, we need to make API calls to the server
      // This is where hybrid execution would be implemented
      return this.executeWithServerFallback(diagram, options, unsupportedNodes);
    }

    // Execute locally for client-safe diagrams
    this.currentExecution = this.executionEngine.execute(diagram, options);
    return this.currentExecution;
  }

  canExecute(diagram: Diagram): boolean {
    const nodeTypes = diagram.nodes.map(node => node.type);
    return nodeTypes.every(nodeType => this.executorFactory.canExecute(nodeType));
  }

  async stop(): Promise<void> {
    if (this.currentExecution) {
      await this.executionEngine.stop();
    }
  }

  /**
   * Execute diagram with server fallback for unsupported nodes
   * This implements hybrid execution by delegating server-only nodes to the backend
   */
  private async executeWithServerFallback(
    diagram: Diagram, 
    options: ExecutionOptions,
    unsupportedNodes: string[]
  ): Promise<ExecutionResult> {
    // For now, call the existing backend API for full execution
    // In a future implementation, this could do true hybrid execution
    const response = await fetch('/api/run-diagram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(diagram)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server execution failed: ${response.status} ${errorText}`);
    }

    const result = await response.json();
    
    // Convert server response to ExecutionResult format
    return {
      success: true,
      context: result.context || result,
      metadata: {
        executionId: result.execution_id || '',
        startTime: Date.now(),
        totalCost: result.total_cost || 0,
        nodeCount: diagram.nodes.length,
        status: 'completed'
      },
      finalOutputs: result.context?.nodeOutputs || {},
      errors: []
    };
  }

  /**
   * Get unsupported node types for the client environment
   */
  private getUnsupportedNodes(diagram: Diagram): string[] {
    return diagram.nodes
      .map(node => node.type)
      .filter(nodeType => !this.executorFactory.canExecute(nodeType));
  }

  /**
   * Get supported node types in client environment
   */
  getSupportedNodeTypes(): string[] {
    return this.executorFactory.getSupportedNodeTypes();
  }

  /**
   * Check if a specific node type can be executed locally
   */
  canExecuteNodeType(nodeType: string): boolean {
    return this.executorFactory.canExecute(nodeType);
  }
}

/**
 * Create a browser-safe execution orchestrator
 */
export function createBrowserExecutionOrchestrator(): BrowserExecutionOrchestrator {
  return new StandardBrowserOrchestrator();
}

/**
 * Execute a diagram in the browser with automatic server fallback
 */
export async function executeDiagramInBrowser(
  diagram: Diagram,
  options: ExecutionOptions = {}
): Promise<ExecutionResult> {
  const orchestrator = createBrowserExecutionOrchestrator();
  return orchestrator.execute(diagram, options);
}