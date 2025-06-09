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
}

interface UseWebSocketEventBusReturn {
  isConnected: boolean;
  isReconnecting: boolean;
  send: (message: WSMessage) => void;
  on: <T = unknown>(eventType: string, callback: EventCallback<T>) => void;
  onPattern: (pattern: RegExp, callback: EventCallback) => void;
  connect: () => void;
  disconnect: () => void;
  waitForConnection: (timeout?: number) => Promise<void>;
}

export function useWebSocketEventBus(options?: UseWebSocketEventBusOptions): UseWebSocketEventBusReturn {
  const { autoConnect = true, debug = false } = options || {};
  const unsubscribesRef = useRef<Set<UnsubscribeFunction>>(new Set());
  const [connectionState, setConnectionState] = useState(() => wsEventBus.getConnectionState());

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

  const stableWaitForConnection = useEvent(async (timeout?: number) => {
    return wsEventBus.waitForConnection(timeout);
  });

  // Subscribe to connection state changes
  useEffect(() => {
    const unsubscribe = onConnectionStateChange(setConnectionState);
    return unsubscribe;
  }, []);

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

  return {
    isConnected: connectionState.isConnected,
    isReconnecting: connectionState.isReconnecting,
    send: stableSend,
    on: stableOn,
    onPattern: stableOnPattern,
    connect: stableConnect,
    disconnect: stableDisconnect,
    waitForConnection: stableWaitForConnection,
  };
}