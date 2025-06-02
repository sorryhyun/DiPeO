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
    // Create custom stream manager for hybrid execution
    const streamManager = createStoreIntegratedStreamManager();
    
    // Create a custom execution engine that can handle hybrid execution
    const hybridEngine = new ExecutionEngine(
      {
        createExecutor: (nodeType: string) => {
          if (this.executorFactory.canExecute(nodeType)) {
            return this.executorFactory.createExecutor(nodeType);
          }
          // Return a proxy executor that makes server API calls
          return this.createServerProxyExecutor(nodeType);
        },
        canExecute: () => true, // We handle all nodes via proxy
        getSupportedNodeTypes: () => [...this.executorFactory.getSupportedNodeTypes(), ...unsupportedNodes]
      },
      streamManager
    );

    // Execute the diagram with hybrid approach
    this.currentExecution = hybridEngine.execute(diagram, options);
    return this.currentExecution;
  }

  /**
   * Create a proxy executor that delegates to server API for server-only nodes
   */
  private createServerProxyExecutor(nodeType: string): any {
    return {
      validateInputs: (_node: any, _inputs: any) => {
        // Basic validation - server will do detailed validation
        return { isValid: true, errors: [] };
      },
      
      execute: async (node: any, inputs: any, context: any) => {
        // Map node types to API endpoints
        const nodeTypeToEndpoint: Record<string, string> = {
          'person_job': '/api/nodes/personjob/execute',
          'personJobNode': '/api/nodes/personjob/execute',
          'person_batch_job': '/api/nodes/personbatchjob/execute',
          'personBatchJobNode': '/api/nodes/personbatchjob/execute',
          'db': '/api/nodes/db/execute',
          'dbNode': '/api/nodes/db/execute'
        };

        const endpoint = nodeTypeToEndpoint[nodeType];
        if (!endpoint) {
          throw new Error(`No API endpoint defined for node type: ${nodeType}`);
        }

        // Prepare payload based on node type
        const payload = this.prepareServerPayload(node, inputs, context);

        // Make API call to server
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Server execution failed for ${nodeType}: ${response.status} ${errorText}`);
        }

        const result = await response.json();
        
        // Return executor result format
        return {
          output: result.output,
          cost: result.cost || 0,
          metadata: result.metadata || {}
        };
      }
    };
  }

  /**
   * Prepare payload for server API call based on node type
   */
  private prepareServerPayload(node: any, inputs: any, context: any): any {
    const basePayload = {
      node_id: node.id,
      inputs: inputs,
      context: {
        nodeOutputs: context.nodeOutputs || {},
        nodeExecutionCounts: context.nodeExecutionCounts || {}
      }
    };

    // Add node-specific data
    if (node.type === 'personJobNode' || node.type === 'person_job') {
      return {
        ...basePayload,
        person: node.data.person || {},
        prompt: node.data.prompt || '',
        node_config: {
          max_iteration: node.data.max_iteration,
          forget: node.data.forget
        }
      };
    } else if (node.type === 'dbNode' || node.type === 'db') {
      return {
        ...basePayload,
        sub_type: node.data.subType || 'file',
        source_details: node.data.sourceDetails || ''
      };
    }

    return basePayload;
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