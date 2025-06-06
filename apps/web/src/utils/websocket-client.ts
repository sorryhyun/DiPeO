/**
 * WebSocket client wrapper for real-time bidirectional communication
 */

export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

export type MessageHandler = (message: WSMessage) => void;
export type ConnectionHandler = (event: CustomEvent) => void;

export interface WebSocketClientOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
}

export class WebSocketClient extends EventTarget {
  private ws: WebSocket | null = null;
  private readonly url: string;
  private readonly messageHandlers = new Map<string, Set<MessageHandler>>();
  private messageQueue: WSMessage[] = [];
  
  // Reconnection settings
  private readonly reconnectInterval: number;
  private readonly maxReconnectInterval: number;
  private readonly reconnectDecay: number;
  private readonly maxReconnectAttempts: number;
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  
  // State
  private forcedClose = false;
  private readonly debug: boolean;
  
  constructor(options: WebSocketClientOptions = {}) {
    super();
    
    // Set connection URL
    this.url = options.url || this.getDefaultWebSocketUrl();
    
    // Set reconnection parameters with exponential backoff
    this.reconnectInterval = options.reconnectInterval || 1000; // Start with 1 second
    this.maxReconnectInterval = options.maxReconnectInterval || 30000; // Max 30 seconds
    this.reconnectDecay = options.reconnectDecay || 1.5; // Exponential backoff factor
    this.maxReconnectAttempts = options.maxReconnectAttempts || Infinity;
    this.debug = options.debug || false;
  }
  
  private getDefaultWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = import.meta.env.VITE_API_PORT || '8000';
    return `${protocol}//${host}:${port}/api/ws`;
  }
  
  private log(...args: unknown[]): void {
    if (this.debug) {
      console.log('[WebSocket]', ...args);
    }
  }
  
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.log('Already connected');
      return;
    }
    
    this.forcedClose = false;
    this.ws = new WebSocket(this.url);
    this.setupEventHandlers();
  }
  
  private setupEventHandlers(): void {
    if (!this.ws) return;
    
    this.ws.onopen = () => {
      this.log('Connected');
      this.reconnectAttempts = 0;
      this.dispatchEvent(new CustomEvent('connected'));
      
      // Send queued messages
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        if (message) {
          this.send(message);
        }
      }
      
      // Send initial subscribe message for monitoring
      this.send({ type: 'subscribe_monitor' });
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        this.log('Received:', message.type, message);
        
        // Dispatch to specific type handlers
        const handlers = this.messageHandlers.get(message.type);
        if (handlers) {
          handlers.forEach(handler => {
            try {
              handler(message);
            } catch (error) {
              console.error('Handler error:', error);
            }
          });
        }
        
        // Dispatch generic message event
        this.dispatchEvent(new CustomEvent('message', { detail: message }));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.dispatchEvent(new CustomEvent('error', { detail: error }));
    };
    
    this.ws.onclose = (event) => {
      this.log('Disconnected', { code: event.code, reason: event.reason });
      this.ws = null;
      this.dispatchEvent(new CustomEvent('disconnected', { detail: event }));
      
      if (!this.forcedClose) {
        this.scheduleReconnect();
      }
    };
  }
  
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.log('Max reconnection attempts reached');
      this.dispatchEvent(new CustomEvent('reconnectFailed'));
      return;
    }
    
    // Calculate delay with exponential backoff
    const delay = Math.min(
      this.reconnectInterval * Math.pow(this.reconnectDecay, this.reconnectAttempts),
      this.maxReconnectInterval
    );
    
    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }
  
  send(message: WSMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.log('Sending:', message.type, message);
      this.ws.send(JSON.stringify(message));
    } else {
      this.log('Queuing message:', message.type);
      this.messageQueue.push(message);
    }
  }
  
  /**
   * Subscribe to specific message types or connection events
   */
  on(type: 'connected' | 'disconnected' | 'error' | 'message' | 'reconnectFailed', handler: ConnectionHandler): this;
  on(type: string, handler: MessageHandler): this;
  on(type: string, handler: ConnectionHandler | MessageHandler): this {
    if (['connected', 'disconnected', 'error', 'message', 'reconnectFailed'].includes(type)) {
      // Use addEventListener for connection events
      this.addEventListener(type, handler as EventListener);
    } else {
      // Use message handlers for message types
      if (!this.messageHandlers.has(type)) {
        this.messageHandlers.set(type, new Set());
      }
      this.messageHandlers.get(type)!.add(handler as MessageHandler);
    }
    return this;
  }
  
  /**
   * Unsubscribe from specific message types or connection events
   */
  off(type: 'connected' | 'disconnected' | 'error' | 'message' | 'reconnectFailed', handler: ConnectionHandler): this;
  off(type: string, handler: MessageHandler): this;
  off(type: string, handler: ConnectionHandler | MessageHandler): this {
    if (['connected', 'disconnected', 'error', 'message', 'reconnectFailed'].includes(type)) {
      // Use removeEventListener for connection events
      this.removeEventListener(type, handler as EventListener);
    } else {
      // Use message handlers for message types
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        handlers.delete(handler as MessageHandler);
        if (handlers.size === 0) {
          this.messageHandlers.delete(type);
        }
      }
    }
    return this;
  }
  
  disconnect(): void {
    this.forcedClose = true;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.messageQueue = [];
    this.messageHandlers.clear();
  }
  
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
  
  getReadyState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED;
  }
}

// Singleton instance
let wsClient: WebSocketClient | null = null;

export function getWebSocketClient(options?: WebSocketClientOptions): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient(options);
  }
  return wsClient;
}

export function disconnectWebSocketClient(): void {
  if (wsClient) {
    wsClient.disconnect();
    wsClient = null;
  }
}