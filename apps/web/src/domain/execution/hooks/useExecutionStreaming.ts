import { useEffect, useRef } from 'react';
import { useExecutionGraphQL } from './useExecutionGraphQL';
import { getConnectionStatus } from '@/lib/graphql/client';

interface UseExecutionStreamingProps {
  executionId: string | null;
  skip?: boolean;
  onConnectionLoss?: () => void;
}

/**
 * Unified hook for execution streaming using GraphQL subscriptions for all execution types
 * (both CLI-launched and web-launched executions)
 */
export function useExecutionStreaming({ executionId, skip = false, onConnectionLoss }: UseExecutionStreamingProps) {
  // Use GraphQL subscriptions for all execution types
  const graphqlResult = useExecutionGraphQL({ 
    executionId, 
    skip
  });

  const lastConnectionStatus = useRef<boolean>(true);

  // Monitor WebSocket connection status
  useEffect(() => {
    if (skip || !executionId) return;

    const checkConnection = setInterval(() => {
      const { isConnected } = getConnectionStatus();
      
      // If connection was lost and we had an active execution
      if (lastConnectionStatus.current && !isConnected) {
        console.log('[ExecutionStreaming] WebSocket connection lost during execution');
        onConnectionLoss?.();
      }
      
      lastConnectionStatus.current = isConnected;
    }, 500); // Check every 500ms for faster response

    return () => clearInterval(checkConnection);
  }, [skip, executionId, onConnectionLoss]);

  const { isConnected } = getConnectionStatus();

  return {
    // Mutations from GraphQL
    executeDiagram: graphqlResult.executeDiagram,
    controlExecution: graphqlResult.controlExecution,
    submitInteractiveResponse: graphqlResult.submitInteractiveResponse,
    
    // Subscription data from GraphQL
    executionUpdates: graphqlResult.executionUpdates,
    nodeUpdates: graphqlResult.nodeUpdates,
    interactivePrompts: graphqlResult.interactivePrompts,
    
    // Connection status based on actual WebSocket state
    isConnected,
    connectionError: !isConnected ? 'WebSocket disconnected' : null,
    usingMonitoringStream: false, // Always false since we're using GraphQL only
  };
}