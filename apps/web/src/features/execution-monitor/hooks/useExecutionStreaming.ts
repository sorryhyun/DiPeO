import { useEffect, useState } from 'react';
import { useExecutionGraphQL } from './useExecutionGraphQL';
import { useDirectStreamingSSE } from './useDirectStreamingSSE';
import { useUnifiedStore } from '@/core/store/unifiedStore';

interface UseExecutionStreamingProps {
  executionId: string | null;
  skip?: boolean;
}

/**
 * Unified hook for execution streaming that automatically selects between
 * SSE (for CLI-launched executions) and GraphQL subscriptions (for web-launched executions)
 */
export function useExecutionStreaming({ executionId, skip = false }: UseExecutionStreamingProps) {
  const [useDirectStreaming, setUseDirectStreaming] = useState(false);
  const [executionUpdates, setExecutionUpdates] = useState<any>(null);
  const [nodeUpdates, setNodeUpdates] = useState<any>(null);
  const [interactivePrompts, setInteractivePrompts] = useState<any>(null);

  // Check if this execution was launched from CLI (indicated by monitor mode)
  useEffect(() => {
    // Use SSE streaming when in monitor mode (CLI executions)
    const store = useUnifiedStore.getState();
    setUseDirectStreaming(store.isMonitorMode);
  }, []);

  // GraphQL subscriptions (for web-launched executions)
  const graphqlResult = useExecutionGraphQL({ 
    executionId, 
    skip: skip || useDirectStreaming // Skip if using SSE
  });

  // SSE streaming (for CLI-launched executions)
  const { isConnected: sseConnected, error: sseError } = useDirectStreamingSSE({
    executionId,
    skip: skip || !useDirectStreaming, // Skip if not using SSE
    onExecutionUpdate: (update) => setExecutionUpdates(update),
    onNodeUpdate: (update) => setNodeUpdates(update),
    onInteractivePrompt: (prompt) => setInteractivePrompts(prompt),
  });

  // Use appropriate data source
  const currentExecutionUpdates = useDirectStreaming ? executionUpdates : graphqlResult.executionUpdates;
  const currentNodeUpdates = useDirectStreaming ? nodeUpdates : graphqlResult.nodeUpdates;
  const currentInteractivePrompts = useDirectStreaming ? interactivePrompts : graphqlResult.interactivePrompts;

  return {
    // Mutations (always from GraphQL)
    executeDiagram: graphqlResult.executeDiagram,
    controlExecution: graphqlResult.controlExecution,
    submitInteractiveResponse: graphqlResult.submitInteractiveResponse,
    
    // Subscription data (from SSE or GraphQL)
    executionUpdates: currentExecutionUpdates,
    nodeUpdates: currentNodeUpdates,
    interactivePrompts: currentInteractivePrompts,
    
    // Connection status
    isConnected: useDirectStreaming ? sseConnected : true,
    connectionError: useDirectStreaming ? sseError : null,
    usingDirectStreaming: useDirectStreaming,
  };
}