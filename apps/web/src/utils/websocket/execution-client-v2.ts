/**
 * WebSocket Execution Client v2 - Refactored to use Event Bus pattern
 * 
 * Provides WebSocket-based execution with bidirectional communication,
 * using the centralized event bus for better separation of concerns.
 */

import { produce } from 'immer';
import { wsEventBus, sendWebSocketMessage, waitForWebSocketConnection } from './event-bus';
import type { 
  WSMessage,
  InteractivePromptData,
  DiagramData,
  ExecutionOptions,
  ExecutionUpdate,
  ExecutionResult
} from '@/types';

/**
 * WebSocket-based execution client using Event Bus pattern
 */
export class ExecutionClientV2 {
  private currentExecutionId: string | null = null;
  private executionResolvers = new Map<string, {
    resolve: (result: ExecutionResult) => void;
    reject: (error: Error) => void;
  }>();
  private executionContext = new Map<string, Record<string, unknown>>();
  private executionTokens = new Map<string, number>();
  private interactivePromptHandler: ((prompt: InteractivePromptData) => void) | null = null;
  private unsubscribeFunctions: Array<() => void> = [];
  
  constructor() {
    this.setupHandlers();
  }
  
  private setupHandlers(): void {
    // Handle execution updates
    this.unsubscribeFunctions.push(
      wsEventBus.on('execution_started', this.handleExecutionStarted.bind(this)),
      wsEventBus.on('node_start', this.handleNodeUpdate.bind(this)),
      wsEventBus.on('node_complete', this.handleNodeUpdate.bind(this)),
      wsEventBus.on('node_skipped', this.handleNodeUpdate.bind(this)),
      wsEventBus.on('node_error', this.handleNodeUpdate.bind(this)),
      wsEventBus.on('execution_complete', this.handleExecutionComplete.bind(this)),
      wsEventBus.on('execution_error', this.handleExecutionError.bind(this)),
      wsEventBus.on('execution_aborted', this.handleExecutionAborted.bind(this)),
      
      // Control response handlers
      wsEventBus.on('node_paused', this.handleControlResponse.bind(this)),
      wsEventBus.on('node_resumed', this.handleControlResponse.bind(this)),
      wsEventBus.on('node_skip_requested', this.handleControlResponse.bind(this)),
      wsEventBus.on('execution_abort_requested', this.handleControlResponse.bind(this)),
      
      // Interactive prompt handlers
      wsEventBus.on('interactive_prompt', this.handleInteractivePrompt.bind(this)),
      wsEventBus.on('interactive_response_received', this.handleControlResponse.bind(this)),
      wsEventBus.on('interactive_prompt_timeout', this.handleControlResponse.bind(this))
    );
  }
  
  private handleExecutionStarted(message: WSMessage): void {
    const executionId = message.execution_id as string;
    if (executionId) {
      this.executionContext.set(executionId, {});
      this.executionTokens.set(executionId, 0);
    }
  }
  
  private handleNodeUpdate(message: WSMessage): void {
    const executionId = message.execution_id as string;
    if (!executionId) return;
    
    // Update context if provided
    if (message.context) {
      const currentContext = this.executionContext.get(executionId) || {};
      this.executionContext.set(executionId, { ...currentContext, ...message.context as Record<string, unknown> });
    }
    
    // Update token count if provided
    if (typeof message.token_count === 'number') {
      const currentTokens = this.executionTokens.get(executionId) || 0;
      this.executionTokens.set(executionId, currentTokens + message.token_count);
    }
  }
  
  private handleExecutionComplete(message: WSMessage): void {
    const executionId = message.execution_id as string;
    if (!executionId) return;
    
    const resolver = this.executionResolvers.get(executionId);
    if (resolver) {
      const context = message.context as Record<string, unknown> || this.executionContext.get(executionId) || {};
      const totalTokens = message.total_token_count as number || this.executionTokens.get(executionId) || 0;
      
      resolver.resolve({
        context,
        totalTokens,
        executionId,
        metadata: {
          totalTokens,
          executionTime: message.duration as number
        }
      });
      
      this.cleanup(executionId);
    }
  }
  
  private handleExecutionError(message: WSMessage): void {
    const executionId = message.execution_id as string;
    const error = message.error as string || 'Unknown execution error';
    
    if (executionId) {
      const resolver = this.executionResolvers.get(executionId);
      if (resolver) {
        resolver.reject(new Error(error));
        this.cleanup(executionId);
      }
    }
  }
  
  private handleExecutionAborted(message: WSMessage): void {
    const executionId = message.execution_id as string;
    if (executionId) {
      const resolver = this.executionResolvers.get(executionId);
      if (resolver) {
        resolver.reject(new Error('Execution was aborted'));
        this.cleanup(executionId);
      }
    }
  }
  
  private handleControlResponse(message: WSMessage): void {
    console.log('Control response:', message.type, message);
  }
  
  private handleInteractivePrompt(message: WSMessage): void {
    if (this.interactivePromptHandler) {
      this.interactivePromptHandler({
        nodeId: message.nodeId as string,
        executionId: (message.executionId as string) || this.currentExecutionId || '',
        prompt: message.prompt as string,
        context: message.context as InteractivePromptData['context']
      });
    }
  }
  
  /**
   * Send interactive response
   */
  sendInteractiveResponse(nodeId: string, response: string): void {
    if (!this.currentExecutionId) {
      console.warn('No active execution for interactive response');
      return;
    }
    
    sendWebSocketMessage({
      type: 'interactive_response',
      nodeId,
      executionId: this.currentExecutionId,
      response
    });
  }
  
  /**
   * Set handler for interactive prompts
   */
  setInteractivePromptHandler(handler: ((prompt: InteractivePromptData) => void) | null): void {
    this.interactivePromptHandler = handler;
  }
  
  private cleanup(executionId: string): void {
    this.executionResolvers.delete(executionId);
    this.executionContext.delete(executionId);
    this.executionTokens.delete(executionId);
    if (this.currentExecutionId === executionId) {
      this.currentExecutionId = null;
    }
  }
  
  /**
   * Execute a diagram using WebSocket streaming
   */
  async execute(
    diagram: DiagramData, 
    options: ExecutionOptions = {},
    onUpdate?: (update: ExecutionUpdate) => void
  ): Promise<ExecutionResult> {
    // Ensure WebSocket is connected
    await waitForWebSocketConnection(5000);
    
    // Set up update handler if provided
    let updateUnsubscribe: (() => void) | null = null;
    if (onUpdate) {
      // Subscribe to all execution-related events
      updateUnsubscribe = wsEventBus.onPattern(/^(node_|execution_)/, (message) => {
        // Convert WebSocket message to ExecutionUpdate format
        const update: ExecutionUpdate = {
          type: message.type,
          execution_id: message.execution_id as string,
          nodeId: message.nodeId as string,
          nodeType: message.node_type as string,
          output: message.output,
          output_preview: message.output_preview as string,
          context: message.context as Record<string, unknown>,
          totalTokens: message.total_tokens as number,
          tokens: message.tokens as number,
          error: message.error as string,
          timestamp: message.timestamp as string,
          conversationId: message.conversation_id as string,
          message: message.message
        };
        
        onUpdate(update);
      });
    }
    
    try {
      // Prepare request payload using immer
      const requestPayload = produce({} as { diagram: DiagramData; options: ExecutionOptions }, draft => {
        draft.diagram = {
          nodes: diagram.nodes || [],
          arrows: diagram.arrows || [],
          persons: diagram.persons || [],
          apiKeys: diagram.apiKeys || []
        };
        draft.options = {
          continueOnError: options.continueOnError ?? false,
          allowPartial: options.allowPartial ?? false,
          debugMode: options.debugMode ?? false
        };
      });
      
      // Send execution request
      sendWebSocketMessage({
        type: 'execute_diagram',
        diagram: requestPayload.diagram,
        options: requestPayload.options
      });
      
      // Wait for execution to complete
      return await new Promise<ExecutionResult>((resolve, reject) => {
        // Generate a temporary ID until we get the real one
        const tempId = `temp_${Date.now()}`;
        
        // Store resolver
        this.executionResolvers.set(tempId, { resolve, reject });
        
        // Set up handler to catch execution_started and update ID
        const startUnsubscribe = wsEventBus.on('execution_started', (message) => {
          if (message.execution_id) {
            const realId = message.execution_id as string;
            
            // Move resolver to real ID
            const resolver = this.executionResolvers.get(tempId);
            if (resolver) {
              this.executionResolvers.delete(tempId);
              this.executionResolvers.set(realId, resolver);
              this.currentExecutionId = realId;
            }
            
            startUnsubscribe();
          }
        });
        
        // Set timeout
        setTimeout(() => {
          if (this.executionResolvers.has(tempId)) {
            this.executionResolvers.delete(tempId);
            reject(new Error('Execution timeout'));
          }
        }, 300000); // 5 minute timeout
      });
      
    } finally {
      // Clean up update handler
      if (updateUnsubscribe) {
        updateUnsubscribe();
      }
    }
  }
  
  /**
   * Pause a specific node
   */
  pauseNode(nodeId: string): void {
    if (!this.currentExecutionId) {
      console.warn('No active execution to pause');
      return;
    }
    
    sendWebSocketMessage({
      type: 'pause_node',
      nodeId,
      executionId: this.currentExecutionId
    });
  }
  
  /**
   * Resume a paused node
   */
  resumeNode(nodeId: string): void {
    if (!this.currentExecutionId) {
      console.warn('No active execution to resume');
      return;
    }
    
    sendWebSocketMessage({
      type: 'resume_node',
      nodeId,
      executionId: this.currentExecutionId
    });
  }
  
  /**
   * Skip a node
   */
  skipNode(nodeId: string): void {
    if (!this.currentExecutionId) {
      console.warn('No active execution to skip node');
      return;
    }
    
    sendWebSocketMessage({
      type: 'skip_node',
      nodeId,
      executionId: this.currentExecutionId
    });
  }
  
  /**
   * Abort the current execution
   */
  abort(): void {
    if (!this.currentExecutionId) {
      console.warn('No active execution to abort');
      return;
    }
    
    sendWebSocketMessage({
      type: 'abort_execution',
      executionId: this.currentExecutionId
    });
  }
  
  /**
   * Check if execution is currently running
   */
  isRunning(): boolean {
    return this.currentExecutionId !== null;
  }
  
  /**
   * Get current execution ID
   */
  getCurrentExecutionId(): string | null {
    return this.currentExecutionId;
  }
  
  /**
   * Cleanup all subscriptions
   */
  destroy(): void {
    this.unsubscribeFunctions.forEach(fn => fn());
    this.unsubscribeFunctions = [];
    this.interactivePromptHandler = null;
  }
}

// Singleton instance
let executionClient: ExecutionClientV2 | null = null;

/**
 * Get or create WebSocket execution client instance
 */
export function getWebSocketExecutionClient(): ExecutionClientV2 {
  if (!executionClient) {
    executionClient = new ExecutionClientV2();
  }
  return executionClient;
}

/**
 * Destroy execution client instance
 */
export function destroyWebSocketExecutionClient(): void {
  if (executionClient) {
    executionClient.destroy();
    executionClient = null;
  }
}