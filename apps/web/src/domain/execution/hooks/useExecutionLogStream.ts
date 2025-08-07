import { useState, useCallback, useEffect } from 'react';
import { executionId } from '@/infrastructure/types';
import { useExecutionUpdatesSubscription } from '@/__generated__/graphql';

interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
  logger: string;
  node_id?: string;
}

/**
 * Hook for execution log streaming via GraphQL subscription
 */
export function useExecutionLogStream(executionIdParam: ReturnType<typeof executionId> | null) {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Subscribe to execution logs via GraphQL
  const { data } = useExecutionUpdatesSubscription({
    variables: { execution_id: executionIdParam || '' },
    skip: !executionIdParam,
  });

  // Append new log entries as they arrive
  useEffect(() => {
    if (data?.execution_updates) {
      const update = data.execution_updates;
      // Check if this is a log event
      if (update.event_type === 'log' && update.data) {
        const logData = update.data;
        if (typeof logData === 'object' && logData !== null) {
          // Convert the log data to LogEntry format
          const newLog: LogEntry = {
            level: logData.level || 'INFO',
            message: logData.message || '',
            timestamp: logData.timestamp || new Date().toISOString(),
            logger: logData.logger || '',
            node_id: logData.node_id,
          };
          setLogs(prev => [...prev, newLog]);
        }
      }
    }
  }, [data]);

  // Clear logs when execution changes
  useEffect(() => {
    clearLogs();
  }, [executionIdParam, clearLogs]);

  return {
    logs,
    clearLogs,
  };
}