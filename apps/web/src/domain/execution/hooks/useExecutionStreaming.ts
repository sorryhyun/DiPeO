import { useExecutionGraphQL } from './useExecutionGraphQL';

interface UseExecutionStreamingProps {
  executionId: string | null;
  skip?: boolean;
}

/**
 * Unified hook for execution streaming using GraphQL subscriptions for all execution types
 * (both CLI-launched and web-launched executions)
 */
export function useExecutionStreaming({ executionId, skip = false }: UseExecutionStreamingProps) {
  // Use GraphQL subscriptions for all execution types
  const graphqlResult = useExecutionGraphQL({ 
    executionId, 
    skip
  });

  return {
    // Mutations from GraphQL
    executeDiagram: graphqlResult.executeDiagram,
    controlExecution: graphqlResult.controlExecution,
    submitInteractiveResponse: graphqlResult.submitInteractiveResponse,
    
    // Subscription data from GraphQL
    executionUpdates: graphqlResult.executionUpdates,
    nodeUpdates: graphqlResult.nodeUpdates,
    interactivePrompts: graphqlResult.interactivePrompts,
    
    // Connection status (GraphQL subscriptions are considered always connected when active)
    isConnected: true,
    connectionError: null,
    usingMonitoringStream: false, // Always false since we're using GraphQL only
  };
}