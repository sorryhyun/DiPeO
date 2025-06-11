/**
 * WebSocket Event Bus - Centralized event handling with pub/sub pattern
 * Provides unified reconnection logic and shared connection state
 */

import { Client, getWebSocketClient } from './client';
import type { WSMessage } from '@/types';
import { toast } from 'sonner';
import { logger } from '../logger';

export type EventCallback<T = any> = (data: T) => void;
export type UnsubscribeFunction = () => void;

interface ConnectionState {
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempts: number;
  lastError?: Error;
}

class WebSocketEventBus {
  private static instance: WebSocketEventBus;
  private client: Client | null = null;
  private listeners = new Map<string, Set<EventCallback>>();
  private connectionListeners = new Set<EventCallback<ConnectionState>>();
  private connectionState: ConnectionState = {
    isConnected: false,
    isReconnecting: false,
    reconnectAttempts: 0,
  };
  private debug = false;

  private constructor() {}

  static getInstance(): WebSocketEventBus {
    if (!WebSocketEventBus.instance) {
      WebSocketEventBus.instance = new WebSocketEventBus();
    }
    return WebSocketEventBus.instance;
  }

  /**
   * Initialize the WebSocket connection
   */
  connect(options?: { debug?: boolean }): void {
    if (this.client?.isConnected()) {
      return;
    }

    this.debug = options?.debug || false;
    this.client = getWebSocketClient({ debug: this.debug });
    
    // Set up connection event handlers
    this.client
      .on('connected', () => {
        this.updateConnectionState({
          isConnected: true,
          isReconnecting: false,
          reconnectAttempts: 0,
        });
        toast.success('Connected to server');
      })
      .on('disconnected', () => {
        this.updateConnectionState({
          isConnected: false,
          isReconnecting: true,
        });
        toast.warning('Disconnected from server. Reconnecting...');
      })
      .on('reconnectFailed', () => {
        this.updateConnectionState({
          isConnected: false,
          isReconnecting: false,
        });
        toast.error('Failed to reconnect to server');
      })
      .on('error', (event) => {
        const error = new Error('WebSocket error');
        this.updateConnectionState({
          lastError: error,
        });
        logger.error('WebSocket error:', event);
      })
      .on('message', (event) => {
        const message = (event as CustomEvent<WSMessage>).detail;
        this.emit(message.type, message);
      });

    this.client.connect();
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.client?.disconnect();
    this.client = null;
    this.updateConnectionState({
      isConnected: false,
      isReconnecting: false,
      reconnectAttempts: 0,
    });
  }

  /**
   * Send a message through WebSocket
   */
  send(message: WSMessage): void {
    if (!this.client) {
      logger.error('WebSocket client not initialized');
      return;
    }
    this.client.send(message);
  }

  /**
   * Subscribe to a specific event type
   */
  on<T = any>(eventType: string, callback: EventCallback<T>): UnsubscribeFunction {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    
    const callbacks = this.listeners.get(eventType)!;
    callbacks.add(callback);

    // Return unsubscribe function
    return () => {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.listeners.delete(eventType);
      }
    };
  }

  /**
   * Subscribe to all events matching a pattern
   */
  onPattern(pattern: RegExp, callback: EventCallback): UnsubscribeFunction {
    const patternCallback = (eventType: string, data: any) => {
      if (pattern.test(eventType)) {
        callback({ type: eventType, ...data });
      }
    };

    // Subscribe to all future events
    const originalEmit = this.emit.bind(this);
    this.emit = (eventType: string, data: any) => {
      patternCallback(eventType, data);
      originalEmit(eventType, data);
    };

    // Return unsubscribe function
    return () => {
      // Restore original emit
      this.emit = originalEmit;
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionStateChange(callback: EventCallback<ConnectionState>): UnsubscribeFunction {
    this.connectionListeners.add(callback);
    
    // Immediately call with current state
    callback(this.connectionState);

    return () => {
      this.connectionListeners.delete(callback);
    };
  }

  /**
   * Emit an event to all listeners
   */
  private emit(eventType: string, data: any): void {
    if (this.debug) {
      logger.debug(`[EventBus] Emit: ${eventType}`, data);
    }

    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          logger.error(`Error in event handler for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Update connection state and notify listeners
   */
  private updateConnectionState(updates: Partial<ConnectionState>): void {
    this.connectionState = {
      ...this.connectionState,
      ...updates,
    };

    this.connectionListeners.forEach(callback => {
      try {
        callback(this.connectionState);
      } catch (error) {
        logger.error('Error in connection state listener:', error);
      }
    });
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return { ...this.connectionState };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState.isConnected;
  }

  /**
   * Wait for connection to be established
   */
  async waitForConnection(timeout = 5000): Promise<void> {
    if (this.isConnected()) {
      return;
    }

    return new Promise((resolve, reject) => {
      const unsubscribe = this.onConnectionStateChange((state) => {
        if (state.isConnected) {
          unsubscribe();
          resolve();
        }
      });

      setTimeout(() => {
        unsubscribe();
        if (!this.isConnected()) {
          reject(new Error('Connection timeout'));
        }
      }, timeout);
    });
  }
}

// Export singleton instance
export const wsEventBus = WebSocketEventBus.getInstance();

// Export convenience functions
export const connectWebSocket = (options?: { debug?: boolean }) => wsEventBus.connect(options);
export const disconnectWebSocket = () => wsEventBus.disconnect();
export const sendWebSocketMessage = (message: WSMessage) => wsEventBus.send(message);
export const onWebSocketEvent = <T = any>(eventType: string, callback: EventCallback<T>) => wsEventBus.on(eventType, callback);
export const onWebSocketPattern = (pattern: RegExp, callback: EventCallback) => wsEventBus.onPattern(pattern, callback);
export const onConnectionStateChange = (callback: EventCallback<ConnectionState>) => wsEventBus.onConnectionStateChange(callback);
export const getConnectionState = () => wsEventBus.getConnectionState();
export const isWebSocketConnected = () => wsEventBus.isConnected();
export const waitForWebSocketConnection = (timeout?: number) => wsEventBus.waitForConnection(timeout);