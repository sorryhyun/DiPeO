import { useState, useCallback, useRef, useEffect } from 'react';
import { ApolloError, FetchResult, Observable, SubscriptionOptions } from '@apollo/client';
import type { Subscription } from 'zen-observable-ts';
import { toast } from 'sonner';

export type StreamState<T> = {
  data: T | null;
  buffer: T[];
  connected: boolean;
  connecting: boolean;
  error: Error | null;
  lastUpdate: Date | null;
};

export type StreamProtocol = 'graphql' | 'sse' | 'websocket';

export type StreamOptions<T> = {
  protocol: StreamProtocol;
  endpoint?: string;
  subscription?: SubscriptionOptions;
  bufferSize?: number;
  reconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  showToasts?: boolean;
  onConnect?: () => void;
  onDisconnect?: (reason?: string) => void;
  onMessage?: (data: T) => void;
  onError?: (error: Error) => void;
  transform?: (raw: any) => T;
};

export type UseStreamReturn<T> = {
  data: T | null;
  buffer: T[];
  connected: boolean;
  connecting: boolean;
  error: Error | null;
  
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => void;
  clearBuffer: () => void;
  clearError: () => void;
  
  lastUpdate: Date | null;
  reconnectAttempts: number;
};

const DEFAULT_OPTIONS = {
  bufferSize: 100,
  reconnect: true,
  reconnectDelay: 3000,
  maxReconnectAttempts: 5,
  showToasts: false,
};

export function useStream<T = any>(
  streamId: string,
  options: StreamOptions<T>
): UseStreamReturn<T> {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
  const {
    protocol,
    endpoint,
    subscription,
    bufferSize,
    reconnect,
    reconnectDelay,
    maxReconnectAttempts,
    showToasts,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
    transform = (x: any) => x as T,
  } = mergedOptions;
  
  const [state, setState] = useState<StreamState<T>>({
    data: null,
    buffer: [],
    connected: false,
    connecting: false,
    error: null,
    lastUpdate: null,
  });
  
  const connectionRef = useRef<EventSource | WebSocket | Subscription | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const isMountedRef = useRef(true);
  
  const addToBuffer = useCallback((data: T) => {
    setState(prev => {
      const newBuffer = [...prev.buffer, data];
      if (newBuffer.length > bufferSize!) {
        newBuffer.shift();
      }
      return {
        ...prev,
        data,
        buffer: newBuffer,
        lastUpdate: new Date(),
      };
    });
  }, [bufferSize]);
  
  const handleMessage = useCallback((rawData: any) => {
    if (!isMountedRef.current) return;
    
    try {
      const data = transform(rawData);
      addToBuffer(data);
      onMessage?.(data);
    } catch (error) {
      console.error(`Failed to process stream message:`, error);
      if (showToasts) {
        toast.error('Failed to process stream message');
      }
    }
  }, [transform, addToBuffer, onMessage, showToasts]);
  
  const handleError = useCallback((error: Error) => {
    if (!isMountedRef.current) return;
    
    setState(prev => ({
      ...prev,
      error,
      connecting: false,
    }));
    
    if (showToasts) {
      toast.error(`Stream error: ${error.message}`);
    }
    
    onError?.(error);
    
    if (reconnect && reconnectAttempts.current < maxReconnectAttempts!) {
      reconnectAttempts.current++;
      reconnectTimeoutRef.current = setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, reconnectDelay);
    }
  }, [showToasts, onError, reconnect, maxReconnectAttempts, reconnectDelay]);
  
  const connectSSE = useCallback(() => {
    if (!endpoint) {
      handleError(new Error('SSE endpoint not provided'));
      return;
    }
    
    const eventSource = new EventSource(endpoint);
    connectionRef.current = eventSource;
    
    eventSource.onopen = () => {
      if (!isMountedRef.current) return;
      setState(prev => ({
        ...prev,
        connected: true,
        connecting: false,
        error: null,
      }));
      reconnectAttempts.current = 0;
      onConnect?.();
    };
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (error) {
        handleMessage(event.data);
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      connectionRef.current = null;
      setState(prev => ({
        ...prev,
        connected: false,
        connecting: false,
      }));
      handleError(new Error('SSE connection failed'));
    };
  }, [endpoint, handleMessage, handleError, onConnect]);
  
  const connectWebSocket = useCallback(() => {
    if (!endpoint) {
      handleError(new Error('WebSocket endpoint not provided'));
      return;
    }
    
    const ws = new WebSocket(endpoint);
    connectionRef.current = ws;
    
    ws.onopen = () => {
      if (!isMountedRef.current) return;
      setState(prev => ({
        ...prev,
        connected: true,
        connecting: false,
        error: null,
      }));
      reconnectAttempts.current = 0;
      onConnect?.();
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (error) {
        handleMessage(event.data);
      }
    };
    
    ws.onerror = (event) => {
      handleError(new Error('WebSocket error'));
    };
    
    ws.onclose = (event) => {
      connectionRef.current = null;
      setState(prev => ({
        ...prev,
        connected: false,
        connecting: false,
      }));
      onDisconnect?.(event.reason);
      
      if (event.code !== 1000 && reconnect) {
        handleError(new Error(`WebSocket closed: ${event.reason || 'Unknown reason'}`));
      }
    };
  }, [endpoint, handleMessage, handleError, onConnect, onDisconnect, reconnect]);
  
  const connectGraphQL = useCallback(() => {
    if (!subscription) {
      handleError(new Error('GraphQL subscription not provided'));
      return;
    }
    
    console.warn('GraphQL subscription support requires Apollo Client setup');
    setState(prev => ({
      ...prev,
      connecting: false,
      error: new Error('GraphQL subscriptions not implemented in this example'),
    }));
  }, [subscription, handleError]);
  
  const connect = useCallback(() => {
    if (state.connected || state.connecting) return;
    
    setState(prev => ({
      ...prev,
      connecting: true,
      error: null,
    }));
    
    switch (protocol) {
      case 'sse':
        connectSSE();
        break;
      case 'websocket':
        connectWebSocket();
        break;
      case 'graphql':
        connectGraphQL();
        break;
      default:
        handleError(new Error(`Unsupported protocol: ${protocol}`));
    }
  }, [state.connected, state.connecting, protocol, connectSSE, connectWebSocket, connectGraphQL, handleError]);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (connectionRef.current) {
      if (connectionRef.current instanceof EventSource) {
        connectionRef.current.close();
      } else if (connectionRef.current instanceof WebSocket) {
        connectionRef.current.close(1000, 'User disconnect');
      } else if ('unsubscribe' in connectionRef.current) {
        connectionRef.current.unsubscribe();
      }
      connectionRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      connected: false,
      connecting: false,
    }));
    
    onDisconnect?.('User initiated');
  }, [onDisconnect]);
  
  const send = useCallback((message: any) => {
    if (!state.connected || !connectionRef.current) {
      console.warn('Cannot send message: not connected');
      return;
    }
    
    if (connectionRef.current instanceof WebSocket) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      connectionRef.current.send(data);
    } else {
      console.warn('Send is only supported for WebSocket connections');
    }
  }, [state.connected]);
  
  const clearBuffer = useCallback(() => {
    setState(prev => ({
      ...prev,
      buffer: [],
    }));
  }, []);
  
  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);
  
  useEffect(() => {
    isMountedRef.current = true;
    
    return () => {
      isMountedRef.current = false;
      disconnect();
    };
  }, []);
  
  return {
    data: state.data,
    buffer: state.buffer,
    connected: state.connected,
    connecting: state.connecting,
    error: state.error,
    
    connect,
    disconnect,
    send,
    clearBuffer,
    clearError,
    
    lastUpdate: state.lastUpdate,
    reconnectAttempts: reconnectAttempts.current,
  };
}