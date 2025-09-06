import { useEffect, useRef } from 'react';
import { useApolloClient } from '@apollo/client';
import { ExecutionUpdatesDocument } from '@/__generated__/graphql';
import type { StoreApi } from 'zustand';
import type { ExecutionLocalStore } from './executionLocalStore';

interface ExecutionUpdateEvent {
  execution_id: string;
  event_type: string;
  data: any;
  timestamp: string;
}

export function useRunSubscription({
  executionId,
  store
}: {
  executionId: string;
  store: StoreApi<ExecutionLocalStore>;
}) {
  const client = useApolloClient();
  const subscriptionRef = useRef<any>(null);

  useEffect(() => {
    if (!executionId) return;

    // Clear any existing subscription
    if (subscriptionRef.current) {
      subscriptionRef.current.unsubscribe();
      subscriptionRef.current = null;
    }

    // Set the execution ID in the store
    store.getState().setExecutionId(executionId);

    // Create the subscription
    const subscription = client.subscribe({
      query: ExecutionUpdatesDocument,
      variables: { execution_id: executionId },
    }).subscribe({
      next: ({ data }) => {
        if (data?.execution_updates) {
          applyExecutionUpdate(store, data.execution_updates);
        }
      },
      error: (error) => {
        console.error('[Board] Subscription error for execution', executionId, error);
      },
    });

    subscriptionRef.current = subscription;

    return () => {
      if (subscriptionRef.current) {
        subscriptionRef.current.unsubscribe();
        subscriptionRef.current = null;
      }
    };
  }, [executionId, client, store]);
}

function applyExecutionUpdate(
  store: StoreApi<ExecutionLocalStore>,
  event: ExecutionUpdateEvent
) {
  const { event_type, data, timestamp } = event;
  const state = store.getState();

  switch (event_type) {
    case 'EXECUTION_STARTED':
      state.setRunning(true);
      state.setStartedAt(new Date(timestamp).getTime());
      if (data?.diagram_name) {
        state.setDiagramData(
          data.diagram_name,
          data.nodes || [],
          data.edges || []
        );
      }
      break;

    case 'EXECUTION_COMPLETED':
      state.setRunning(false);
      state.setFinishedAt(new Date(timestamp).getTime());
      // Clear all running nodes
      state.runningNodes.forEach(nodeId => {
        state.removeRunningNode(nodeId);
      });
      break;

    case 'EXECUTION_FAILED':
      state.setRunning(false);
      state.setFinishedAt(new Date(timestamp).getTime());
      // Clear all running nodes
      state.runningNodes.forEach(nodeId => {
        state.removeRunningNode(nodeId);
      });
      if (data?.error) {
        console.error('[Board] Execution failed:', data.error);
      }
      break;

    case 'NODE_STARTED':
      if (data?.node_id) {
        state.addRunningNode(data.node_id);
        state.updateNodeState(data.node_id, {
          status: 'running',
          timestamp: new Date(timestamp).getTime(),
        });
      }
      break;

    case 'NODE_COMPLETED':
      if (data?.node_id) {
        state.removeRunningNode(data.node_id);
        state.updateNodeState(data.node_id, {
          status: 'completed',
          timestamp: new Date(timestamp).getTime(),
          outputs: data.outputs,
        });
      }
      break;

    case 'NODE_FAILED':
      if (data?.node_id) {
        state.removeRunningNode(data.node_id);
        state.updateNodeState(data.node_id, {
          status: 'failed',
          timestamp: new Date(timestamp).getTime(),
          error: data.error || 'Node execution failed',
        });
      }
      break;

    case 'NODE_SKIPPED':
      if (data?.node_id) {
        state.updateNodeState(data.node_id, {
          status: 'skipped',
          timestamp: new Date(timestamp).getTime(),
        });
      }
      break;

    case 'EXECUTION_PAUSED':
      state.setRunning(false);
      break;

    case 'EXECUTION_RESUMED':
      state.setRunning(true);
      break;

    case 'DIAGRAM_LOADED':
      if (data?.diagram_name && data?.nodes && data?.edges) {
        state.setDiagramData(data.diagram_name, data.nodes, data.edges);
      }
      break;

    default:
      // Handle other event types as needed
      console.debug('[Board] Unhandled event type:', event_type, data);
  }
}
