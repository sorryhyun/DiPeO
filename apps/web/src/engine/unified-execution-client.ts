/**
 * Unified Execution Client - Simple API wrapper for V2 backend execution
 * 
 * Replaces the complex frontend execution orchestrator with a simple
 * client that delegates all execution to the backend unified engine.
 */

import { getApiUrl, API_ENDPOINTS } from '@/shared/utils/apiConfig';
import type { Node, Arrow } from '@/shared/types';

export interface DiagramData {
  nodes: Node[];
  arrows: Arrow[];
  persons?: any[];
  apiKeys?: any[];
}

export interface ExecutionOptions {
  continueOnError?: boolean;
  allowPartial?: boolean;
  debugMode?: boolean;
}

export interface ExecutionUpdate {
  type: 'execution_started' | 'node_start' | 'node_complete' | 'execution_complete' | 'execution_error' | 'conversation_update';
  execution_id?: string;
  nodeId?: string;
  output_preview?: string;
  context?: Record<string, any>;
  total_cost?: number;
  error?: string;
  timestamp?: string;
  conversationId?: string;
  message?: any;
}

export interface ExecutionResult {
  context: Record<string, any>;
  total_cost?: number;
  execution_id?: string;
  metadata?: {
    totalCost?: number;
    executionTime?: number;
  };
}

/**
 * Simple execution client that uses the V2 unified backend API
 */
export class UnifiedExecutionClient {
  private abortController: AbortController | null = null;
  
  /**
   * Execute a diagram using the V2 unified backend with SSE streaming
   */
  async execute(
    diagram: DiagramData, 
    options: ExecutionOptions = {},
    onUpdate?: (update: ExecutionUpdate) => void
  ): Promise<ExecutionResult> {
    // Abort any previous execution
    this.abort();
    
    // Create new abort controller
    this.abortController = new AbortController();
    
    try {
      const response = await fetch(getApiUrl(API_ENDPOINTS.RUN_DIAGRAM), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...diagram,
          options
        }),
        signal: this.abortController.signal
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Execution failed: ${response.status} - ${errorText}`);
      }
      
      // Handle SSE streaming
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('Response body is not readable');
      }
      
      let context: Record<string, any> = {};
      let totalCost = 0;
      let executionId: string | undefined;
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                const update: ExecutionUpdate = data;
                
                // Track execution state
                if (update.execution_id) {
                  executionId = update.execution_id;
                }
                
                if (update.context) {
                  context = { ...context, ...update.context };
                }
                
                if (update.total_cost !== undefined) {
                  totalCost = update.total_cost;
                }
                
                // Send update to callback
                if (onUpdate) {
                  onUpdate(update);
                }
                
                // Handle execution completion
                if (update.type === 'execution_complete') {
                  return {
                    context: update.context || context,
                    total_cost: update.total_cost || totalCost,
                    execution_id: update.execution_id || executionId,
                    metadata: {
                      totalCost: update.total_cost || totalCost
                    }
                  };
                }
                
                // Handle execution errors
                if (update.type === 'execution_error') {
                  throw new Error(update.error || 'Unknown execution error');
                }
                
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line, parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
      // Return final result if no explicit completion event
      return {
        context,
        total_cost: totalCost,
        execution_id: executionId,
        metadata: {
          totalCost
        }
      };
      
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new Error('Execution was cancelled');
      }
      throw error;
    } finally {
      this.abortController = null;
    }
  }
  
  /**
   * Abort the current execution
   */
  abort(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
  
  /**
   * Check if execution is currently running
   */
  isRunning(): boolean {
    return this.abortController !== null;
  }
  
  /**
   * Get execution capabilities from the backend
   */
  async getCapabilities(): Promise<any> {
    const response = await fetch(getApiUrl(API_ENDPOINTS.EXECUTION_CAPABILITIES));
    if (!response.ok) {
      throw new Error(`Failed to get capabilities: ${response.status}`);
    }
    return response.json();
  }
  
  /**
   * Health check for the V2 API
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(getApiUrl(API_ENDPOINTS.HEALTH));
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }
}

/**
 * Create a new unified execution client instance
 */
export function createUnifiedExecutionClient(): UnifiedExecutionClient {
  return new UnifiedExecutionClient();
}

/**
 * Global client instance for convenience
 */
export const unifiedExecutionClient = createUnifiedExecutionClient();