import { useEffect, useState, useRef, useCallback } from 'react';
import { ExecutionStatus, NodeExecutionStatus, EventType } from '@dipeo/domain-models';

interface SSEEvent {
  type: string;
  execution_id: string;
  data?: any;
}

interface UseDirectStreamingSSEProps {
  executionId: string | null;
  skip?: boolean;
  onExecutionUpdate?: (update: any) => void;
  onNodeUpdate?: (update: any) => void;
  onInteractivePrompt?: (prompt: any) => void;
}

/**
 * Hook for direct SSE streaming when launched from CLI
 * This bypasses the message router and connects directly to the SSE endpoint
 */
export function useDirectStreamingSSE({ 
  executionId, 
  skip = false,
  onExecutionUpdate,
  onNodeUpdate,
  onInteractivePrompt
}: UseDirectStreamingSSEProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const executionCompletedRef = useRef(false);

  const connect = useCallback(() => {
    if (!executionId || skip) return;

    try {
      const eventSource = new EventSource(`/sse/executions/${executionId}`);
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
          
          // Route events to appropriate handlers
          switch (data.type) {
            case EventType.EXECUTION_STATUS_CHANGED:
              if (onExecutionUpdate && data.data) {
                // Check if execution has completed
                if (data.data.status === ExecutionStatus.COMPLETED || 
                    data.data.status === ExecutionStatus.FAILED ||
                    data.data.status === ExecutionStatus.ABORTED) {
                  executionCompletedRef.current = true;
                }
                onExecutionUpdate({
                  status: data.data.status,
                  error: data.data.error,
                  tokenUsage: data.data.token_usage,
                });
              }
              break;
              
            case EventType.NODE_STATUS_CHANGED:
              if (onNodeUpdate && data.data) {
                onNodeUpdate({
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
              if (onInteractivePrompt && data.data) {
                onInteractivePrompt({
                  execution_id: data.execution_id,
                  node_id: data.data.node_id,
                  prompt: data.data.prompt,
                  timeout_seconds: data.data.timeout_seconds,
                });
              }
              break;
              
            case EventType.EXECUTION_ERROR:
              if (onExecutionUpdate && data.data) {
                onExecutionUpdate({
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

      eventSource.onerror = (event) => {
        // Check if we're in CLI mode
        const params = new URLSearchParams(window.location.search);
        const isCliMode = params.get('monitor') === 'true' || !!params.get('executionId');
        
        // If execution has completed and we're in CLI mode, don't log errors or reconnect
        if (executionCompletedRef.current && isCliMode) {
          console.log('[SSE] Server shutting down after execution completion, not reconnecting');
          setIsConnected(false);
          return;
        }
        
        console.error('[SSE] Connection error:', event);
        setIsConnected(false);
        setError('SSE connection failed');
        
        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < 5 && !executionCompletedRef.current) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectAttemptsRef.current += 1;
          
          console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
          reconnectTimeoutRef.current = setTimeout(() => {
            if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
              connect();
            }
          }, delay);
        }
      };
    } catch (e) {
      console.error('[SSE] Failed to create EventSource:', e);
      setError('Failed to establish SSE connection');
    }
  }, [executionId, skip, onExecutionUpdate, onNodeUpdate, onInteractivePrompt]);

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