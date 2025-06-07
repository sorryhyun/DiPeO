import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  onWebSocketEvent,
  sendWebSocketMessage,
  connectWebSocket,
  disconnectWebSocket,
  wsEventBus
} from '@/utils/websocket/event-bus';
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
 * WebSocket connection management hook using Event Bus pattern
 * Migrated from direct WebSocket client to centralized Event Bus
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
  const [connectionState, setConnectionState] = useState(() => wsEventBus.getConnectionState());
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [lastError, setLastError] = useState<Error | null>(null);
  
  // Refs for message handlers
  const messageHandlersRef = useRef<Map<string, Set<(message: WSMessage) => void>>>(new Map());

  // Update connection state
  useEffect(() => {
    return wsEventBus.onConnectionStateChange(setConnectionState);
  }, []);

  // Derive connection state string
  const connectionStateString: WebSocketState['connectionState'] = 
    connectionState.isReconnecting ? 'reconnecting' : 
    connectionState.isConnected ? 'connected' : 
    'disconnected';

  // Set up connection event handlers
  useEffect(() => {
    // Handle connection events
    const unsubscribes: Array<() => void> = [];

    unsubscribes.push(onWebSocketEvent('connected', () => {
      setLastError(null);
      onConnected?.();
    }));

    unsubscribes.push(onWebSocketEvent('disconnected', () => {
      onDisconnected?.();
    }));

    unsubscribes.push(onWebSocketEvent('error', (message: WSMessage) => {
      const error = new Error(message.error as string || 'Unknown error');
      setLastError(error);
      onError?.(error);
    }));

    unsubscribes.push(onWebSocketEvent('reconnect_failed', () => {
      onReconnectFailed?.();
    }));

    return () => {
      unsubscribes.forEach(fn => fn());
    };
  }, [onConnected, onDisconnected, onError, onReconnectFailed]);

  // Set up message handling
  useEffect(() => {
    // Subscribe to all message types
    return wsEventBus.onPattern(/.*/, (message: WSMessage) => {
      setLastMessage(message);
      
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
    });
  }, [onMessage]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && !connectionState.isConnected) {
      connectWebSocket(clientOptions);
    }
  }, [autoConnect]); // Only on mount

  // Actions
  const connect = useCallback(() => {
    if (!connectionState.isConnected) {
      connectWebSocket(clientOptions);
    }
  }, [connectionState.isConnected, clientOptions]);

  const disconnect = useCallback(() => {
    disconnectWebSocket();
  }, []);

  const send = useCallback((message: WSMessage | Record<string, unknown>) => {
    // Ensure message has a type
    const wsMessage: WSMessage = 'type' in message 
      ? message as WSMessage
      : { type: 'unknown', ...message };

    sendWebSocketMessage(wsMessage);
  }, []);

  const subscribe = useCallback((eventType: string, handler: (message: WSMessage) => void) => {
    // Add handler to our map
    if (!messageHandlersRef.current.has(eventType)) {
      messageHandlersRef.current.set(eventType, new Set());
    }
    messageHandlersRef.current.get(eventType)!.add(handler);

    // Also subscribe to Event Bus for this specific event type
    const unsubscribe = onWebSocketEvent(eventType, handler);

    // Return unsubscribe function that removes from both
    return () => {
      const handlers = messageHandlersRef.current.get(eventType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlersRef.current.delete(eventType);
        }
      }
      unsubscribe();
    };
  }, []);

  const reconnect = useCallback(async () => {
    // Event Bus handles reconnection automatically, but we can force it
    disconnectWebSocket();
    // Wait a bit before reconnecting
    await new Promise(resolve => setTimeout(resolve, 100));
    connectWebSocket(clientOptions);
  }, [clientOptions]);

  const state: WebSocketState = {
    isConnected: connectionState.isConnected,
    connectionState: connectionStateString,
    lastMessage,
    lastError,
  };

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
export type { WSMessage } from '@/types';