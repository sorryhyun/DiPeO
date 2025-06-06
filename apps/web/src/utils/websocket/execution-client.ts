/**
 * WebSocket Execution Client - WebSocket-based execution for real-time control
 * 
 * Replaces SSE-based execution with WebSocket for bidirectional communication,
 * enabling pause/resume/skip/abort capabilities.
 */

import { produce } from 'immer';
import { getWebSocketClient, Client } from './client';
import type { 
  Node, 
  Arrow, 
  Person, 
  ApiKey, 
  WSMessage,
  InteractivePromptData
} from '@/types';
import type {
  DiagramData,
  ExecutionOptions,
  ExecutionUpdate,
  ExecutionResult
} from '@/types/api';

/**
 * WebSocket-based execution client with real-time control capabilities
 */
export class ExecutionClient {
  private wsClient: Client;
  private currentExecutionId: string | null = null;
  private executionResolvers = new Map<string, {
    resolve: (result: ExecutionResult) => void;
    reject: (error: Error) => void;
  }>();
  private executionContext = new Map<string, Record<string, unknown>>();
  private executionCost = new Map<string, number>();
  private interactivePromptHandler: ((prompt: InteractivePromptData) => void) | null = null;
  
  constructor(wsClient?: Client) {
    this.wsClient = wsClient || getWebSocketClient({ debug: true });
    this.setupHandlers();
  }
  
  private setupHandlers(): void {
    // Handle execution updates
    this.wsClient.on('execution_started', this.handleExecutionStarted.bind(this));
    this.wsClient.on('node_start', this.handleNodeUpdate.bind(this));
    this.wsClient.on('node_complete', this.handleNodeUpdate.bind(this));
    this.wsClient.on('node_skipped', this.handleNodeUpdate.bind(this));
    this.wsClient.on('node_error', this.handleNodeUpdate.bind(this));
    this.wsClient.on('execution_complete', this.handleExecutionComplete.bind(this));
    this.wsClient.on('execution_error', this.handleExecutionError.bind(this));
    this.wsClient.on('execution_aborted', this.handleExecutionAborted.bind(this));
    
    // Control response handlers
    this.wsClient.on('node_paused', this.handleControlResponse.bind(this));
    this.wsClient.on('node_resumed', this.handleControlResponse.bind(this));
    this.wsClient.on('node_skip_requested', this.handleControlResponse.bind(this));
    this.wsClient.on('execution_abort_requested', this.handleControlResponse.bind(this));
    
    // Interactive prompt handlers
    this.wsClient.on('interactive_prompt', this.handleInteractivePrompt.bind(this));
    this.wsClient.on('interactive_response_received', this.handleControlResponse.bind(this));
    this.wsClient.on('interactive_prompt_timeout', this.handleControlResponse.bind(this));
  }
  
  private handleExecutionStarted(message: WSMessage): void {
    const executionId = message.execution_id as string;
    if (executionId) {
      this.executionContext.set(executionId, {});
      this.executionCost.set(executionId, 0);
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
    
    // Update cost if provided
    if (typeof message.cost === 'number') {
      const currentCost = this.executionCost.get(executionId) || 0;
      this.executionCost.set(executionId, currentCost + message.cost);
    }
  }
  
  private handleExecutionComplete(message: WSMessage): void {
    const executionId = message.execution_id as string;
    if (!executionId) return;
    
    const resolver = this.executionResolvers.get(executionId);
    if (resolver) {
      const context = message.context as Record<string, unknown> || this.executionContext.get(executionId) || {};
      const totalCost = message.total_cost as number || this.executionCost.get(executionId) || 0;
      
      resolver.resolve({
        context,
        totalCost: totalCost,
        executionId: executionId,
        metadata: {
          totalCost,
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
    
    this.wsClient.send({
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
    if (!this.wsClient.isConnected()) {
      this.wsClient.connect();
      
      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 5000);
        
        const handler = () => {
          clearTimeout(timeout);
          this.wsClient.off('connected', handler);
          resolve();
        };
        
        this.wsClient.on('connected', handler);
      });
    }
    
    // Set up update handler if provided
    let messageHandler: ((event: Event) => void) | null = null;
    if (onUpdate) {
      messageHandler = ((event: Event) => {
        const customEvent = event as CustomEvent;
        const message = customEvent.detail as WSMessage;
        
        // Convert WebSocket message to ExecutionUpdate format
        const update: ExecutionUpdate = {
          type: message.type,
          executionId: message.execution_id as string,
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
        
        // Map backend event types to frontend expectations
        if (update.type === 'node_start' && update.nodeId) {
          update.type = 'node_start';
          onUpdate(update);
        } else if (update.type === 'node_complete' && update.nodeId) {
          update.type = 'node_complete';
          onUpdate(update);
        } else {
          onUpdate(update);
        }
      });
      
      this.wsClient.addEventListener('message', messageHandler);
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
      this.wsClient.send({
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
        const startHandler = (message: WSMessage) => {
          if (message.type === 'execution_started' && message.execution_id) {
            const realId = message.execution_id as string;
            
            // Move resolver to real ID
            const resolver = this.executionResolvers.get(tempId);
            if (resolver) {
              this.executionResolvers.delete(tempId);
              this.executionResolvers.set(realId, resolver);
              this.currentExecutionId = realId;
            }
            
            this.wsClient.off('execution_started', startHandler);
          }
        };
        
        this.wsClient.on('execution_started', startHandler);
        
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
      if (messageHandler) {
        this.wsClient.removeEventListener('message', messageHandler);
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
    
    this.wsClient.send({
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
    
    this.wsClient.send({
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
    
    this.wsClient.send({
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
    
    this.wsClient.send({
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
}

/**
 * Create a new WebSocket execution client instance
 */
export function createWebSocketExecutionClient(wsClient?: Client): ExecutionClient {
  return new ExecutionClient(wsClient);
}