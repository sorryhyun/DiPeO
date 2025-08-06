import { useEffect, useState, useRef, useCallback } from 'react';
import { ExecutionStatus, NodeExecutionStatus, EventType } from '@dipeo/models';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';

interface SSEEvent {
  type: string;
  execution_id: string;
  data?: any;
}

interface UseMonitoringStreamSSEProps {
  executionId: string | null;
  skip?: boolean;
  onExecutionUpdate?: (update: any) => void;
  onNodeUpdate?: (update: any) => void;
  onInteractivePrompt?: (prompt: any) => void;
}

/**
 * Hook for monitoring-only SSE streaming when launched from CLI
 * This provides read-only access to execution updates via SSE endpoint
 */
export function useMonitoringStreamSSE({ 
  executionId, 
  skip = false,
  onExecutionUpdate,
  onNodeUpdate,
  onInteractivePrompt
}: UseMonitoringStreamSSEProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const executionCompletedRef = useRef(false);
  
  // Store callbacks in refs to prevent reconnection on every render
  const callbacksRef = useRef({
    onExecutionUpdate,
    onNodeUpdate,
    onInteractivePrompt
  });
  
  // Update refs when callbacks change
  useEffect(() => {
    callbacksRef.current = {
      onExecutionUpdate,
      onNodeUpdate,
      onInteractivePrompt
    };
  }, [onExecutionUpdate, onNodeUpdate, onInteractivePrompt]);

  const connect = useCallback(() => {
    if (!executionId || skip) return;

    // Reset completion flag when connecting
    executionCompletedRef.current = false;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const eventSource = new EventSource(`${apiUrl}/sse/executions/${executionId}`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log(`[SSE] Connected to execution ${executionId}`);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const data: SSEEvent = JSON.parse(event.data);
          
          // Handle connection and heartbeat events
          if (data.type === 'CONNECTION_ESTABLISHED') {
            console.log('[SSE] Connection established with execution');
            return;
          }
          
          if (data.type === 'HEARTBEAT') {
            // Heartbeat received - connection is healthy
            return;
          }
          
          // Route events to appropriate handlers
          switch (data.type) {
            case EventType.EXECUTION_STATUS_CHANGED:
              if (callbacksRef.current.onExecutionUpdate && data.data) {
                console.log('[SSE] Execution status update:', data.data.status);
                // Check if execution has completed
                if (data.data.status === ExecutionStatus.COMPLETED || 
                    data.data.status === ExecutionStatus.FAILED ||
                    data.data.status === ExecutionStatus.ABORTED) {
                  executionCompletedRef.current = true;
                }
                callbacksRef.current.onExecutionUpdate({
                  status: data.data.status,
                  error: data.data.error,
                  tokenUsage: data.data.token_usage,
                });
              }
              break;
              
            case EventType.NODE_STATUS_CHANGED:
              if (callbacksRef.current.onNodeUpdate && data.data) {
                console.log('[SSE] Node status update:', {
                  node_id: data.data.node_id,
                  status: data.data.status,
                  node_type: data.data.node_type
                });
                // Pass data directly without wrapping
                callbacksRef.current.onNodeUpdate({
                  node_id: data.data.node_id,
                  status: data.data.status,
                  node_type: data.data.node_type,
                  output: data.data.output,
                  error: data.data.error,
                  tokens_used: data.data.tokens_used,
                });
              }
              break;
              
            case EventType.INTERACTIVE_PROMPT:
              if (callbacksRef.current.onInteractivePrompt && data.data) {
                callbacksRef.current.onInteractivePrompt({
                  execution_id: data.execution_id,
                  node_id: data.data.node_id,
                  prompt: data.data.prompt,
                  timeout_seconds: data.data.timeout_seconds,
                });
              }
              break;
              
            case EventType.EXECUTION_ERROR:
              if (callbacksRef.current.onExecutionUpdate && data.data) {
                callbacksRef.current.onExecutionUpdate({
                  status: ExecutionStatus.FAILED,
                  error: data.data.error,
                });
              }
              break;
          }
        } catch (e) {
          console.error('[SSE] Error parsing event:', e);
        }
      };

      eventSource.onerror = (_event) => {
        // Check if we're in monitor mode
        const store = useUnifiedStore.getState();
        const isMonitorMode = store.isMonitorMode;
        
        // If execution has completed and we're in monitor mode, don't log errors or reconnect
        if (executionCompletedRef.current && isMonitorMode) {
          console.log('[SSE] Stream closed after execution completion');
          setIsConnected(false);
          return;
        }
        
        // Check if this is a normal closure (readyState === CLOSED)
        if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
          console.log('[SSE] Connection closed normally');
          setIsConnected(false);
          return;
        }
        
        console.warn('[SSE] Connection interrupted');
        setIsConnected(false);
        
        // Only attempt reconnection if we haven't completed and this looks like an unexpected error
        if (reconnectAttemptsRef.current < 3 && !executionCompletedRef.current) {
          const delay = Math.min(2000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;
          
          console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
          reconnectTimeoutRef.current = setTimeout(() => {
            if (eventSourceRef.current?.readyState === EventSource.CLOSED && !executionCompletedRef.current) {
              connect();
            }
          }, delay);
        } else if (reconnectAttemptsRef.current >= 3) {
          setError('Unable to establish stable SSE connection');
          console.error('[SSE] Max reconnection attempts reached');
        }
      };
    } catch (e) {
      console.error('[SSE] Failed to create EventSource:', e);
      setError('Failed to establish SSE connection');
    }
  }, [executionId, skip]); // Removed callbacks from dependencies to prevent reconnection

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('[SSE] Disconnecting');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    reconnect: connect,
    disconnect,
  };
}