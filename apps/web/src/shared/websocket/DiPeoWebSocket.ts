/**
 * Shared WebSocket client for DiPeO
 * Provides high-level methods for diagram execution and monitoring
 */

import { EventEmitter } from 'events';
import { 
  DomainDiagram, 
  ExecutionState, 
  ExecutionMessage,
  WSMessage,
  NodeExecutionState
} from '@/types';
import { Client as WebSocketClient, getWebSocketClient } from '@/utils/websocket/client';
import { logger } from '@/utils/logger';

export interface ExecutionOptions {
  monitor?: boolean;
  debug?: boolean;
  timeout?: number;
  skipInteractive?: boolean;
}

export interface ExecutionResult {
  success: boolean;
  executionId: string;
  results?: Record<string, any>;
  error?: string;
}

export type DiPeoWebSocketEvent = 
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'execution:started'
  | 'execution:completed'
  | 'execution:failed'
  | 'execution:paused'
  | 'execution:resumed'
  | 'node:started'
  | 'node:completed'
  | 'node:failed'
  | 'node:skipped'
  | 'message:received'
  | 'prompt:request'
  | 'prompt:response';

export class DiPeoWebSocket extends EventEmitter {
  private static instances = new Map<string, DiPeoWebSocket>();
  private client: WebSocketClient;
  private executionId: string | null = null;
  private pendingPromises = new Map<string, {
    resolve: (value: any) => void;
    reject: (reason: any) => void;
    timeout?: ReturnType<typeof setTimeout>;
  }>();

  private constructor(private instanceType: string) {
    super();
    this.client = getWebSocketClient({ debug: true });
    this.setupEventHandlers();
  }

  /**
   * Get singleton instance for execution context
   */
  static forExecution(): DiPeoWebSocket {
    return this.getInstance('execution');
  }

  /**
   * Get singleton instance for monitoring context
   */
  static forMonitoring(): DiPeoWebSocket {
    return this.getInstance('monitoring');
  }

  private static getInstance(type: string): DiPeoWebSocket {
    if (!this.instances.has(type)) {
      this.instances.set(type, new DiPeoWebSocket(type));
    }
    return this.instances.get(type)!;
  }

  private setupEventHandlers(): void {
    // Connection events
    this.client.on('connected', () => {
      logger.debug(`[DiPeoWebSocket:${this.instanceType}] Connected`);
      this.emit('connected');
    });

    this.client.on('disconnected', (event) => {
      logger.debug(`[DiPeoWebSocket:${this.instanceType}] Disconnected`, event.detail);
      this.emit('disconnected', event.detail);
    });

    this.client.on('error', (event) => {
      logger.error(`[DiPeoWebSocket:${this.instanceType}] Error`, event.detail);
      this.emit('error', event.detail);
    });

    // Execution messages
    this.client.on('execution_started', (message: ExecutionMessage) => {
      this.executionId = message.data?.executionId;
      this.emit('execution:started', message.data);
    });

    this.client.on('execution_completed', (message: ExecutionMessage) => {
      this.emit('execution:completed', message.data);
      this.resolvePending('execute', message.data);
    });

    this.client.on('execution_failed', (message: ExecutionMessage) => {
      this.emit('execution:failed', message.data);
      this.rejectPending('execute', new Error(message.data?.error || 'Execution failed'));
    });

    this.client.on('execution_paused', (message: ExecutionMessage) => {
      this.emit('execution:paused', message.data);
    });

    this.client.on('execution_resumed', (message: ExecutionMessage) => {
      this.emit('execution:resumed', message.data);
    });

    // Node execution events
    this.client.on('node_started', (message: ExecutionMessage) => {
      this.emit('node:started', message.data);
    });

    this.client.on('node_completed', (message: ExecutionMessage) => {
      this.emit('node:completed', message.data);
    });

    this.client.on('node_failed', (message: ExecutionMessage) => {
      this.emit('node:failed', message.data);
    });

    this.client.on('node_skipped', (message: ExecutionMessage) => {
      this.emit('node:skipped', message.data);
    });

    // Interactive prompts
    this.client.on('prompt_request', (message: ExecutionMessage) => {
      this.emit('prompt:request', message.data);
    });

    // Generic message handler
    this.client.on('message', (event) => {
      this.emit('message:received', event.detail);
    });
  }

  /**
   * Connect to the WebSocket server
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.client.isConnected()) {
        resolve();
        return;
      }

      const onConnected = () => {
        this.client.off('connected', onConnected);
        this.client.off('error', onError);
        resolve();
      };

      const onError = (event: CustomEvent) => {
        this.client.off('connected', onConnected);
        this.client.off('error', onError);
        reject(new Error('Failed to connect'));
      };

      this.client.on('connected', onConnected);
      this.client.on('error', onError);
      this.client.connect();

      // Timeout after 10 seconds
      setTimeout(() => {
        this.client.off('connected', onConnected);
        this.client.off('error', onError);
        reject(new Error('Connection timeout'));
      }, 10000);
    });
  }

  /**
   * Execute a diagram with options
   */
  async execute(diagram: DomainDiagram, options?: ExecutionOptions): Promise<ExecutionResult> {
    await this.connect();

    return this.sendAndWait('execute_diagram', {
      diagram,
      options: {
        monitor: options?.monitor || false,
        debug: options?.debug || false,
        timeout: options?.timeout,
        skipInteractive: options?.skipInteractive || false
      }
    }, 'execute', options?.timeout);
  }

  /**
   * Pause current execution
   */
  async pause(): Promise<void> {
    if (!this.executionId) {
      throw new Error('No active execution');
    }

    await this.send({
      type: 'pause_execution',
      data: { executionId: this.executionId }
    });
  }

  /**
   * Resume paused execution
   */
  async resume(): Promise<void> {
    if (!this.executionId) {
      throw new Error('No active execution');
    }

    await this.send({
      type: 'resume_execution',
      data: { executionId: this.executionId }
    });
  }

  /**
   * Skip current node
   */
  async skipNode(nodeId: string, reason?: string): Promise<void> {
    if (!this.executionId) {
      throw new Error('No active execution');
    }

    await this.send({
      type: 'skip_node',
      data: { 
        executionId: this.executionId,
        nodeId,
        reason 
      }
    });
  }

  /**
   * Stop execution
   */
  async stop(): Promise<void> {
    if (!this.executionId) {
      throw new Error('No active execution');
    }

    await this.send({
      type: 'stop_execution',
      data: { executionId: this.executionId }
    });
  }

  /**
   * Send prompt response
   */
  async sendPromptResponse(nodeId: string, response: string): Promise<void> {
    if (!this.executionId) {
      throw new Error('No active execution');
    }

    await this.send({
      type: 'prompt_response',
      data: {
        executionId: this.executionId,
        nodeId,
        response
      }
    });
  }

  /**
   * Monitor an existing execution
   */
  async monitor(executionId: string): Promise<void> {
    await this.connect();
    this.executionId = executionId;

    await this.send({
      type: 'monitor_execution',
      data: { executionId }
    });
  }

  /**
   * Get execution state
   */
  async getExecutionState(): Promise<ExecutionState | null> {
    if (!this.executionId) {
      return null;
    }

    const response = await this.sendAndWait('get_execution_state', {
      executionId: this.executionId
    }, 'execution_state', 5000);

    return response.state;
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.executionId = null;
    this.pendingPromises.clear();
    this.removeAllListeners();
    // Don't actually disconnect the client as it's shared
  }

  /**
   * Send a message through WebSocket
   */
  private async send(message: WSMessage): Promise<void> {
    this.client.send(message);
  }

  /**
   * Send a message and wait for response
   */
  private async sendAndWait<T = any>(
    type: string, 
    data: any, 
    waitKey: string,
    timeout: number = 30000
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeoutHandle = timeout > 0 ? setTimeout(() => {
        this.pendingPromises.delete(waitKey);
        reject(new Error(`Request timeout: ${type}`));
      }, timeout) : undefined;

      this.pendingPromises.set(waitKey, {
        resolve,
        reject,
        timeout: timeoutHandle
      });

      this.send({ type, data });
    });
  }

  /**
   * Resolve a pending promise
   */
  private resolvePending(key: string, value: any): void {
    const pending = this.pendingPromises.get(key);
    if (pending) {
      if (pending.timeout) {
        clearTimeout(pending.timeout);
      }
      this.pendingPromises.delete(key);
      pending.resolve(value);
    }
  }

  /**
   * Reject a pending promise
   */
  private rejectPending(key: string, error: Error): void {
    const pending = this.pendingPromises.get(key);
    if (pending) {
      if (pending.timeout) {
        clearTimeout(pending.timeout);
      }
      this.pendingPromises.delete(key);
      pending.reject(error);
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.client.isConnected();
  }

  /**
   * Get current execution ID
   */
  getExecutionId(): string | null {
    return this.executionId;
  }
}