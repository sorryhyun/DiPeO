import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketStatus {
  CONNECTING: 'connecting';
  CONNECTED: 'connected';
  DISCONNECTED: 'disconnected';
  ERROR: 'error';
}

export const WS_STATUS: WebSocketStatus = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
} as const;

export type WebSocketStatusType = WebSocketStatus[keyof WebSocketStatus];

export interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  shouldReconnect?: () => boolean;
}

export interface UseWebSocketReturn {
  data: any;
  status: WebSocketStatusType;
  error: Event | null;
  lastMessage: MessageEvent | null;
  send: (data: string | object) => void;
  close: () => void;
}

const DEFAULT_OPTIONS: Required<Pick<UseWebSocketOptions, 'reconnectAttempts' | 'reconnectInterval' | 'maxReconnectInterval'>> = {
  reconnectAttempts: 5,
  reconnectInterval: 1000,
  maxReconnectInterval: 30000,
};

export function useWebSocket(url: string, options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnectAttempts = DEFAULT_OPTIONS.reconnectAttempts,
    reconnectInterval = DEFAULT_OPTIONS.reconnectInterval,
    maxReconnectInterval = DEFAULT_OPTIONS.maxReconnectInterval,
    shouldReconnect = () => true,
  } = options;

  const [data, setData] = useState<any>(null);
  const [status, setStatus] = useState<WebSocketStatusType>(WS_STATUS.CONNECTING);
  const [error, setError] = useState<Event | null>(null);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const attemptCountRef = useRef(0);
  const currentIntervalRef = useRef(reconnectInterval);
  const isMountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!isMountedRef.current || socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Skip connection if URL is empty (for development mode)
    if (!url) {
      setStatus(WS_STATUS.DISCONNECTED);
      return;
    }

    try {
      setStatus(WS_STATUS.CONNECTING);
      setError(null);

      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        if (!isMountedRef.current) return;
        
        setStatus(WS_STATUS.CONNECTED);
        attemptCountRef.current = 0;
        currentIntervalRef.current = reconnectInterval;
        onOpen?.();
      };

      socket.onmessage = (event: MessageEvent) => {
        if (!isMountedRef.current) return;

        setLastMessage(event);
        
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
          onMessage?.(parsedData);
        } catch {
          // If parsing fails, treat as plain text
          setData(event.data);
          onMessage?.(event.data);
        }
      };

      socket.onclose = (event) => {
        if (!isMountedRef.current) return;

        setStatus(WS_STATUS.DISCONNECTED);
        onClose?.();

        // Attempt reconnection if conditions are met
        if (
          shouldReconnect() &&
          attemptCountRef.current < reconnectAttempts &&
          !event.wasClean
        ) {
          attemptCountRef.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connect();
            }
          }, currentIntervalRef.current);

          // Exponential backoff
          currentIntervalRef.current = Math.min(
            currentIntervalRef.current * 2,
            maxReconnectInterval
          );
        }
      };

      socket.onerror = (event) => {
        if (!isMountedRef.current) return;

        setStatus(WS_STATUS.ERROR);
        setError(event);
        onError?.(event);
      };
    } catch (err) {
      if (!isMountedRef.current) return;
      
      setStatus(WS_STATUS.ERROR);
      const errorEvent = new Event('error');
      setError(errorEvent);
      onError?.(errorEvent);
    }
  }, [url, onMessage, onError, onOpen, onClose, shouldReconnect, reconnectAttempts, reconnectInterval, maxReconnectInterval]);

  const send = useCallback((data: string | object) => {
    const socket = socketRef.current;
    
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      socket.send(message);
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', data);
    }
  }, []);

  const close = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    const socket = socketRef.current;
    if (socket) {
      socket.close(1000, 'Manual close');
      socketRef.current = null;
    }

    setStatus(WS_STATUS.DISCONNECTED);
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      const socket = socketRef.current;
      if (socket) {
        socket.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  return {
    data,
    status,
    error,
    lastMessage,
    send,
    close,
  };
}