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
  // Provide a dummy execution_id when skipping to avoid GraphQL validation errors
  const { data } = useExecutionUpdatesSubscription({
    variables: { execution_id: executionIdParam || 'dummy-id-for-skip' },
    skip: !executionIdParam,
  });

  // Append new log entries as they arrive
  useEffect(() => {
    if (data?.execution_updates) {
      const update = data.execution_updates;
      
      // Handle batch updates
      if (update.event_type === 'BATCH_UPDATE' && update.data) {
        const batchData = update.data;
        if (batchData.events && Array.isArray(batchData.events)) {
          // Process each event in the batch
          const newLogs: LogEntry[] = [];
          for (const event of batchData.events) {
            if (event.type === 'EXECUTION_LOG' && event.data) {
              const logData = event.data;
              if (typeof logData === 'object' && logData !== null) {
                newLogs.push({
                  level: logData.level || 'INFO',
                  message: logData.message || '',
                  timestamp: logData.timestamp || event.timestamp || new Date().toISOString(),
                  logger: logData.logger || '',
                  node_id: logData.node_id,
                });
              }
            }
          }
          if (newLogs.length > 0) {
            setLogs(prev => [...prev, ...newLogs]);
          }
        }
      }
      // Also handle individual log events (for backward compatibility)
      else if (update.event_type === 'EXECUTION_LOG' && update.data) {
        const logData = update.data;
        if (typeof logData === 'object' && logData !== null) {
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