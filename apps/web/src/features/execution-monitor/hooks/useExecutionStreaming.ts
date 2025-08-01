import { useEffect, useState } from 'react';
import { useExecutionGraphQL } from './useExecutionGraphQL';
import { useMonitoringStreamSSE } from './useMonitoringStreamSSE';
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
  const [useMonitoringStream, setUseMonitoringStream] = useState(false);
  const [executionUpdates, setExecutionUpdates] = useState<any>(null);
  const [nodeUpdates, setNodeUpdates] = useState<any>(null);
  const [interactivePrompts, setInteractivePrompts] = useState<any>(null);

  // Check if this execution was launched from CLI (indicated by monitor mode)
  useEffect(() => {
    // Use SSE streaming when in monitor mode (CLI executions)
    const store = useUnifiedStore.getState();
    setUseMonitoringStream(store.isMonitorMode);
  }, []);

  // GraphQL subscriptions (for web-launched executions)
  const graphqlResult = useExecutionGraphQL({ 
    executionId, 
    skip: skip || useMonitoringStream // Skip if using SSE
  });

  // SSE streaming (for CLI-launched executions)
  const { isConnected: sseConnected, error: sseError } = useMonitoringStreamSSE({
    executionId,
    skip: skip || !useMonitoringStream, // Skip if not using SSE
    onExecutionUpdate: (update) => setExecutionUpdates(update),
    onNodeUpdate: (update) => setNodeUpdates(update),
    onInteractivePrompt: (prompt) => setInteractivePrompts(prompt),
  });

  // Use appropriate data source
  const currentExecutionUpdates = useMonitoringStream ? executionUpdates : graphqlResult.executionUpdates;
  const currentNodeUpdates = useMonitoringStream ? nodeUpdates : graphqlResult.nodeUpdates;
  const currentInteractivePrompts = useMonitoringStream ? interactivePrompts : graphqlResult.interactivePrompts;

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
    isConnected: useMonitoringStream ? sseConnected : true,
    connectionError: useMonitoringStream ? sseError : null,
    usingMonitoringStream: useMonitoringStream,
  };
}