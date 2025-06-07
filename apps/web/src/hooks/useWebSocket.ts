import { useState, useEffect, useCallback, useRef } from 'react';
import { Client, getWebSocketClient } from '@/utils/websocket';
import { WSMessage, WebSocketClientOptions } from '@/types';

export interface WebSocketState {
  isConnected: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'reconnecting';
  lastMessage: WSMessage | null;
  lastError: Error | null;
}

export interface WebSocketActions {
  connect: () => void;
  disconnect: () => void;
  send: (message: WSMessage | Record<string, unknown>) => void;
  subscribe: (eventType: string, handler: (message: WSMessage) => void) => () => void;
  reconnect: () => void;
}

export interface UseWebSocketOptions extends WebSocketClientOptions {
  autoConnect?: boolean;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onMessage?: (message: WSMessage) => void;
  onError?: (error: Error) => void;
  onReconnectFailed?: () => void;
}

/**
 * Low-level WebSocket connection management hook
 * Provides connection state, message handling, and WebSocket actions
 */
export const useWebSocket = (options: UseWebSocketOptions = {}): [WebSocketState, WebSocketActions] => {
  const {
    autoConnect = true,
    onConnected,
    onDisconnected,
    onMessage,
    onError,
    onReconnectFailed,
    ...clientOptions
  } = options;

  // State
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    connectionState: 'disconnected',
    lastMessage: null,
    lastError: null,
  });

  // Refs
  const clientRef = useRef<Client | null>(null);
  const messageHandlersRef = useRef<Map<string, Set<(message: WSMessage) => void>>>(new Map());
  const isComponentMountedRef = useRef(true);

  // Initialize client
  useEffect(() => {
    const client = getWebSocketClient(clientOptions);
    clientRef.current = client;

    // Set up event handlers
    const handleConnected = () => {
      if (!isComponentMountedRef.current) return;
      setState(prev => ({
        ...prev,
        isConnected: true,
        connectionState: 'connected',
        lastError: null,
      }));
      onConnected?.();
    };

    const handleDisconnected = () => {
      if (!isComponentMountedRef.current) return;
      setState(prev => ({
        ...prev,
        isConnected: false,
        connectionState: 'disconnected',
      }));
      onDisconnected?.();
    };

    const handleMessage = (event: Event) => {
      if (!isComponentMountedRef.current) return;
      const customEvent = event as CustomEvent<WSMessage>;
      const message = customEvent.detail;
      
      setState(prev => ({
        ...prev,
        lastMessage: message,
      }));

      // Call registered handlers for this message type
      const handlers = messageHandlersRef.current.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error(`Error in handler for ${message.type}:`, error);
          }
        });
      }

      onMessage?.(message);
    };

    const handleError = (event: Event) => {
      if (!isComponentMountedRef.current) return;
      const customEvent = event as CustomEvent;
      const error = new Error(customEvent.detail as string);
      
      setState(prev => ({
        ...prev,
        lastError: error,
      }));
      onError?.(error);
    };

    const handleReconnectFailed = () => {
      if (!isComponentMountedRef.current) return;
      setState(prev => ({
        ...prev,
        connectionState: 'disconnected',
      }));
      onReconnectFailed?.();
    };

    const handleReconnecting = () => {
      if (!isComponentMountedRef.current) return;
      setState(prev => ({
        ...prev,
        connectionState: 'reconnecting',
      }));
    };

    // Subscribe to events
    client.addEventListener('connected', handleConnected);
    client.addEventListener('disconnected', handleDisconnected);
    client.addEventListener('message', handleMessage);
    client.addEventListener('error', handleError);
    client.addEventListener('reconnectFailed', handleReconnectFailed);
    client.addEventListener('reconnecting', handleReconnecting);

    // Auto-connect if enabled
    if (autoConnect && !client.isConnected()) {
      setState(prev => ({ ...prev, connectionState: 'connecting' }));
      client.connect();
    }

    // Cleanup
    return () => {
      isComponentMountedRef.current = false;
      client.removeEventListener('connected', handleConnected);
      client.removeEventListener('disconnected', handleDisconnected);
      client.removeEventListener('message', handleMessage);
      client.removeEventListener('error', handleError);
      client.removeEventListener('reconnectFailed', handleReconnectFailed);
      client.removeEventListener('reconnecting', handleReconnecting);
    };
  }, [autoConnect, onConnected, onDisconnected, onMessage, onError, onReconnectFailed]);

  // Actions
  const connect = useCallback(() => {
    const client = clientRef.current;
    if (!client) return;

    if (!client.isConnected()) {
      setState(prev => ({ ...prev, connectionState: 'connecting' }));
      client.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    const client = clientRef.current;
    if (!client) return;

    client.disconnect();
  }, []);

  const send = useCallback((message: WSMessage | Record<string, unknown>) => {
    const client = clientRef.current;
    if (!client) return;

    // Ensure message has a type
    const wsMessage: WSMessage = 'type' in message 
      ? message as WSMessage
      : { type: 'unknown', ...message };

    client.send(wsMessage);
  }, []);

  const subscribe = useCallback((eventType: string, handler: (message: WSMessage) => void) => {
    // Add handler to our map
    if (!messageHandlersRef.current.has(eventType)) {
      messageHandlersRef.current.set(eventType, new Set());
    }
    messageHandlersRef.current.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = messageHandlersRef.current.get(eventType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlersRef.current.delete(eventType);
        }
      }
    };
  }, []);

  const reconnect = useCallback(() => {
    const client = clientRef.current;
    if (!client) return;

    setState(prev => ({ ...prev, connectionState: 'reconnecting' }));
    // Client doesn't have a reconnect method, use disconnect and connect
    client.disconnect();
    client.connect();
  }, []);

  const actions: WebSocketActions = {
    connect,
    disconnect,
    send,
    subscribe,
    reconnect,
  };

  return [state, actions];
};

// Re-export for convenience
export { getWebSocketClient } from '@/utils/websocket';
export type { WSMessage } from '@/types';