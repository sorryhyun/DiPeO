import { useEffect, useRef } from 'react';
import { useExecutionUpdatesSubscription, useGetExecutionQuery, EventType } from '@/__generated__/graphql';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { Status, nodeId } from '@/infrastructure/types';

/**
 * Hook that subscribes to execution updates and updates node states in the store.
 * Falls back to polling if subscription doesn't deliver events.
 * This enables real-time node highlighting when diagrams are run from CLI in browser mode.
 */
export function useExecutionSubscriptionHandler(executionIdParam: string | null) {
  const executionActions = useUnifiedStore(state => state);
  const isRunning = useUnifiedStore(state => state.execution.isRunning);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Subscribe to execution updates (primary method)
  const { data, error } = useExecutionUpdatesSubscription({
    variables: { execution_id: executionIdParam || 'dummy-id-for-skip' },
    skip: !executionIdParam,
  });

  // Polling fallback (secondary method)
  const { refetch } = useGetExecutionQuery({
    variables: { execution_id: executionIdParam || 'dummy-id-for-skip' },
    skip: true, // Don't auto-fetch, we'll refetch manually
  });

  // Setup polling as fallback
  useEffect(() => {
    if (!executionIdParam || !isRunning) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      return;
    }

    // Poll every 500ms while execution is running
    pollIntervalRef.current = setInterval(async () => {
      try {
        const result = await refetch({ execution_id: executionIdParam });
        const execution = result.data?.getExecution;

        if (execution?.node_states) {
          // Apply node states from polling
          Object.entries(execution.node_states).forEach(([nodeIdStr, state]: [string, any]) => {
            if (state?.status) {
              const nId = nodeId(nodeIdStr);
              const statusMap: Record<string, Status> = {
                'RUNNING': Status.RUNNING,
                'COMPLETED': Status.COMPLETED,
                'FAILED': Status.FAILED,
                'SKIPPED': Status.SKIPPED,
              };
              // Convert status to uppercase before mapping (database returns lowercase)
              const mappedStatus = statusMap[state.status.toUpperCase()];
              if (mappedStatus) {
                executionActions.updateNodeExecution(nId, {
                  status: mappedStatus,
                  timestamp: Date.now(),
                  error: state.error
                });
              }
            }
          });
        }
      } catch (err) {
        console.error('[SubscriptionHandler] Polling error:', err);
      }
    }, 500);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [executionIdParam, isRunning, refetch, executionActions]);

  // Process subscription updates
  useEffect(() => {
    if (!data?.executionUpdates || !executionIdParam) return;

    const update = data.executionUpdates;
    const eventType = update.type;
    const eventData = update.data || {};

    // Handle node events
    if (eventType === EventType.NODE_STARTED && eventData.node_id) {
      const nId = nodeId(String(eventData.node_id));
      executionActions.updateNodeExecution(nId, {
        status: Status.RUNNING,
        timestamp: Date.now()
      });
    }
    else if (eventType === EventType.NODE_COMPLETED && eventData.node_id) {
      const nId = nodeId(String(eventData.node_id));
      executionActions.updateNodeExecution(nId, {
        status: Status.COMPLETED,
        timestamp: Date.now()
      });
    }
    else if (eventType === EventType.NODE_ERROR && eventData.node_id) {
      const nId = nodeId(String(eventData.node_id));
      executionActions.updateNodeExecution(nId, {
        status: Status.FAILED,
        timestamp: Date.now(),
        error: eventData.error ? String(eventData.error) : undefined
      });
    }
    else if (eventType === EventType.EXECUTION_COMPLETED) {
      executionActions.stopExecution();
    }
  }, [data, executionIdParam, executionActions]);
}
