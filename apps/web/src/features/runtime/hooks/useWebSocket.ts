/**
 * Hook for managing WebSocket connection and monitoring execution events
 */

import { useEffect, useRef, useState } from 'react';
import { WebSocketClient, WSMessage, getWebSocketClient } from '../websocket-client';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  debug?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  send: (message: WSMessage) => void;
  lastMessage: WSMessage | null;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'reconnecting';
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true, debug = false } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<UseWebSocketReturn['connectionState']>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const clientRef = useRef<WebSocketClient | null>(null);
  
  useEffect(() => {
    // Get or create WebSocket client
    const client = getWebSocketClient({ debug });
    clientRef.current = client;
    
    // Set up event handlers
    const handleConnected = () => {
      setIsConnected(true);
      setConnectionState('connected');
      console.log('[useWebSocket] Connected to WebSocket');
    };
    
    const handleDisconnected = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
      console.log('[useWebSocket] Disconnected from WebSocket');
    };
    
    const handleMessage = (event: Event) => {
      const customEvent = event as CustomEvent<WSMessage>;
      setLastMessage(customEvent.detail);
      if (debug) {
        console.log('[useWebSocket] Received message:', customEvent.detail);
      }
    };
    
    const handleError = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.error('[useWebSocket] Error:', customEvent.detail);
    };
    
    const handleReconnectFailed = () => {
      setConnectionState('disconnected');
      console.error('[useWebSocket] Failed to reconnect after maximum attempts');
    };
    
    // Subscribe to events
    client.addEventListener('connected', handleConnected);
    client.addEventListener('disconnected', handleDisconnected);
    client.addEventListener('message', handleMessage);
    client.addEventListener('error', handleError);
    client.addEventListener('reconnectFailed', handleReconnectFailed);
    
    // Auto-connect if enabled
    if (autoConnect && !client.isConnected()) {
      setConnectionState('connecting');
      client.connect();
    }
    
    // Cleanup
    return () => {
      client.removeEventListener('connected', handleConnected);
      client.removeEventListener('disconnected', handleDisconnected);
      client.removeEventListener('message', handleMessage);
      client.removeEventListener('error', handleError);
      client.removeEventListener('reconnectFailed', handleReconnectFailed);
    };
  }, [autoConnect, debug]);
  
  const connect = () => {
    if (clientRef.current && !clientRef.current.isConnected()) {
      setConnectionState('connecting');
      clientRef.current.connect();
    }
  };
  
  const disconnect = () => {
    if (clientRef.current) {
      clientRef.current.disconnect();
    }
  };
  
  const send = (message: WSMessage) => {
    if (clientRef.current) {
      clientRef.current.send(message);
    }
  };
  
  return {
    isConnected,
    connect,
    disconnect,
    send,
    lastMessage,
    connectionState
  };
}

/**
 * Hook to subscribe to specific WebSocket message types
 */
export function useWebSocketMessage<T = unknown>(
  messageType: string,
  handler: (message: WSMessage & { type: string; data?: T }) => void
): void {
  useEffect(() => {
    const client = getWebSocketClient();
    
    const messageHandler = (message: WSMessage) => {
      if (message.type === messageType) {
        handler(message as WSMessage & { type: string; data?: T });
      }
    };
    
    client.on(messageType, messageHandler);
    
    return () => {
      client.off(messageType, messageHandler);
    };
  }, [messageType, handler]);
}