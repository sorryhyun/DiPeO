/**
 * React hook for WebSocket Event Bus
 * Provides easy access to WebSocket functionality with automatic cleanup
 */

import { useEffect, useRef, useState } from 'react';
import {
  wsEventBus,
  connectWebSocket,
  disconnectWebSocket,
  sendWebSocketMessage,
  onWebSocketEvent,
  onWebSocketPattern,
  onConnectionStateChange,
  type EventCallback,
  type UnsubscribeFunction,
} from '@/utils/websocket/event-bus';
import type { WSMessage } from '@/types/runtime';
import { useEvent } from './useEvent';

interface UseWebSocketEventBusOptions {
  autoConnect?: boolean;
  debug?: boolean;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Error) => void;
  onMessage?: (message: WSMessage) => void;
  onReconnectFailed?: () => void;
}

interface UseWebSocketEventBusReturn {
  isConnected: boolean;
  isReconnecting: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'reconnecting';
  lastMessage: WSMessage | null;
  lastError: Error | null;
  send: (message: WSMessage) => void;
  on: <T = unknown>(eventType: string, callback: EventCallback<T>) => void;
  onPattern: (pattern: RegExp, callback: EventCallback) => void;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  waitForConnection: (timeout?: number) => Promise<void>;
}

export function useWebSocketEventBus(options?: UseWebSocketEventBusOptions): UseWebSocketEventBusReturn {
  const { 
    autoConnect = true, 
    debug = false,
    onConnected,
    onDisconnected,
    onError,
    onMessage,
    onReconnectFailed
  } = options || {};
  const unsubscribesRef = useRef<Set<UnsubscribeFunction>>(new Set());
  const [connectionState, setConnectionState] = useState(() => wsEventBus.getConnectionState());
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [lastError, setLastError] = useState<Error | null>(null);

  // Stable callbacks using useEvent
  const stableSend = useEvent((message: WSMessage) => {
    sendWebSocketMessage(message);
  });

  const stableOn = useEvent(<T = unknown>(eventType: string, callback: EventCallback<T>) => {
    const unsubscribe = onWebSocketEvent(eventType, callback);
    unsubscribesRef.current.add(unsubscribe);
  });

  const stableOnPattern = useEvent((pattern: RegExp, callback: EventCallback) => {
    const unsubscribe = onWebSocketPattern(pattern, callback);
    unsubscribesRef.current.add(unsubscribe);
  });

  const stableConnect = useEvent(() => {
    connectWebSocket({ debug });
  });

  const stableDisconnect = useEvent(() => {
    disconnectWebSocket();
  });

  const stableReconnect = useEvent(() => {
    disconnectWebSocket();
    setTimeout(() => {
      connectWebSocket({ debug });
    }, 100);
  });

  const stableWaitForConnection = useEvent(async (timeout?: number) => {
    return wsEventBus.waitForConnection(timeout);
  });

  // Subscribe to connection state changes
  useEffect(() => {
    const unsubscribe = onConnectionStateChange(setConnectionState);
    return unsubscribe;
  }, []);

  // Handle connection events
  useEffect(() => {
    if (!onConnected && !onDisconnected && !onError && !onReconnectFailed) return;

    const unsubscribes: UnsubscribeFunction[] = [];

    if (onConnected) {
      unsubscribes.push(onWebSocketEvent('connected', onConnected));
    }
    if (onDisconnected) {
      unsubscribes.push(onWebSocketEvent('disconnected', onDisconnected));
    }
    if (onError) {
      unsubscribes.push(onWebSocketEvent('error', (event: Error | ErrorEvent | { message?: string }) => {
        const error = event instanceof Error 
          ? event 
          : new Error((event as any)?.message || 'WebSocket error');
        setLastError(error);
        onError(error);
      }));
    }
    if (onReconnectFailed) {
      unsubscribes.push(onWebSocketEvent('reconnectFailed', onReconnectFailed));
    }

    return () => {
      unsubscribes.forEach(fn => fn());
    };
  }, [onConnected, onDisconnected, onError, onReconnectFailed]);

  // Handle message tracking
  useEffect(() => {
    if (!onMessage) return;

    const unsubscribe = onWebSocketPattern(/.*/, (message: WSMessage) => {
      setLastMessage(message);
      onMessage(message);
    });

    return unsubscribe;
  }, [onMessage]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      stableConnect();
    }

    // Cleanup all subscriptions on unmount
    return () => {
      unsubscribesRef.current.forEach(unsubscribe => unsubscribe());
      unsubscribesRef.current.clear();
    };
  }, [autoConnect, stableConnect]);

  // Derive connection state string
  const getConnectionStateString = (): 'connecting' | 'connected' | 'disconnected' | 'reconnecting' => {
    if (connectionState.isConnected) return 'connected';
    if (connectionState.isReconnecting) return 'reconnecting';
    return 'disconnected';
  };

  return {
    isConnected: connectionState.isConnected,
    isReconnecting: connectionState.isReconnecting,
    connectionState: getConnectionStateString(),
    lastMessage,
    lastError,
    send: stableSend,
    on: stableOn,
    onPattern: stableOnPattern,
    connect: stableConnect,
    disconnect: stableDisconnect,
    reconnect: stableReconnect,
    waitForConnection: stableWaitForConnection,
  };
}