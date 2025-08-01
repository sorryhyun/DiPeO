import { useState, useEffect, useCallback, useRef } from 'react';
import { executionId } from '@/core/types';

interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
  logger: string;
  node_id?: string;
}

export function useExecutionLogStream(executionIdParam: ReturnType<typeof executionId> | null) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  useEffect(() => {
    if (!executionIdParam) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Clear logs when starting new execution
    clearLogs();

    // Create new SSE connection
    const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/sse/executions/${executionIdParam}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('[ExecutionLogStream] SSE connection opened');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        console.log('[ExecutionLogStream] Received event:', data.type);
        
        // Handle execution log events
        if (data.type === 'EXECUTION_LOG' && data.data) {
          const logEntry: LogEntry = {
            level: data.data.level || 'INFO',
            message: data.data.message || '',
            timestamp: data.data.timestamp || new Date().toISOString(),
            logger: data.data.logger || 'unknown',
            node_id: data.data.node_id,
          };
          
          console.log('[ExecutionLogStream] Adding log entry:', logEntry);
          setLogs(prev => [...prev, logEntry]);
        }
      } catch (error) {
        console.error('[ExecutionLogStream] Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('[ExecutionLogStream] SSE connection error:', error);
      
      // If the connection is closed, don't try to reconnect
      if (eventSource.readyState === EventSource.CLOSED) {
        console.log('[ExecutionLogStream] SSE connection closed');
        eventSourceRef.current = null;
      }
    };

    // Cleanup on unmount or execution change
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [executionIdParam, clearLogs]);

  return {
    logs,
    clearLogs,
  };
}