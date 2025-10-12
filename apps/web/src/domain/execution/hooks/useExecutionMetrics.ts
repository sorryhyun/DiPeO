import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery, useSubscription } from '@apollo/client';
import { GETEXECUTIONMETRICS_QUERY, EXECUTIONUPDATES_SUBSCRIPTION } from '@/__generated__/queries/all-queries';

interface TokenUsage {
  input: number;
  output: number;
  total: number;
}

interface NodeMetrics {
  node_id: string;
  node_type: string;
  duration_ms: number;
  token_usage: TokenUsage;
  error?: string;
}

interface ExecutionMetrics {
  execution_id: string;
  total_duration_ms: number;
  node_count: number;
  total_token_usage: TokenUsage;
  bottlenecks: Array<{
    node_id: string;
    node_type: string;
    duration_ms: number;
  }>;
  critical_path_length: number;
  parallelizable_groups: number;
  node_breakdown?: NodeMetrics[];
}

interface UseExecutionMetricsResult {
  metrics: ExecutionMetrics | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
  isLive: boolean;
}

export function useExecutionMetrics(executionId: string, enableSubscription = true): UseExecutionMetricsResult {
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(null);
  const [isLive, setIsLive] = useState(false);
  const metricsRef = useRef<ExecutionMetrics | null>(null);

  // Query initial metrics
  const { data, loading, error, refetch } = useQuery(GETEXECUTIONMETRICS_QUERY, {
    variables: { execution_id: executionId },
    skip: !executionId,
    fetchPolicy: 'network-only',
  });

  // Subscribe to real-time updates
  const { data: subscriptionData } = useSubscription(EXECUTIONUPDATES_SUBSCRIPTION, {
    variables: { execution_id: executionId },
    skip: !executionId || !enableSubscription,
    onError: (err) => {
      console.error('Subscription error:', err);
    },
  });

  // Process initial metrics from query
  useEffect(() => {
    if (data?.execution_metrics) {
      const metricsData = data.execution_metrics;
      setMetrics(metricsData);
      metricsRef.current = metricsData;
    }
  }, [data]);

  // Process real-time updates from subscription
  useEffect(() => {
    if (!subscriptionData?.execution_updates) return;

    const update = subscriptionData.execution_updates;

    // Handle metrics in EXECUTION_LOG events
    if (update.event_type === 'EXECUTION_LOG' && update.data?.type === 'metrics') {
      setIsLive(true);

      if (update.data) {
        // Update metrics with new data
        const newMetrics = update.data as ExecutionMetrics;

        // Merge with existing metrics if needed
        setMetrics(prevMetrics => {
          if (!prevMetrics) return newMetrics;

          // Merge node breakdown if it exists
          const mergedNodeBreakdown = newMetrics.node_breakdown || prevMetrics.node_breakdown;

          return {
            ...newMetrics,
            node_breakdown: mergedNodeBreakdown,
          };
        });

        metricsRef.current = newMetrics;
      }
    }

    // Handle NODE_COMPLETED events to update token usage
    if (update.event_type === 'NODE_COMPLETED' && update.data) {
      const nodeData = update.data;

      // Extract token usage from node data if available
      if (nodeData.metrics?.token_usage || nodeData.token_usage) {
        const tokenUsage = nodeData.metrics?.token_usage || nodeData.token_usage;

        setMetrics(prevMetrics => {
          if (!prevMetrics) return null;

          // Update total token usage
          const updatedTotalTokenUsage = {
            input: (prevMetrics.total_token_usage?.input || 0) + (tokenUsage.input || 0),
            output: (prevMetrics.total_token_usage?.output || 0) + (tokenUsage.output || 0),
            total: (prevMetrics.total_token_usage?.total || 0) + (tokenUsage.total || 0),
          };

          // Update node breakdown if node_id is available
          const updatedNodeBreakdown = prevMetrics.node_breakdown || [];
          if (nodeData.node_id) {
            const existingNodeIndex = updatedNodeBreakdown.findIndex(
              n => n.node_id === nodeData.node_id
            );

            if (existingNodeIndex >= 0 && updatedNodeBreakdown[existingNodeIndex]) {
              // Update existing node
              const existingNode = updatedNodeBreakdown[existingNodeIndex];
              updatedNodeBreakdown[existingNodeIndex] = {
                ...existingNode,
                token_usage: tokenUsage,
              };
            } else if (nodeData.node_id) {
              // Add new node only if node_id exists
              updatedNodeBreakdown.push({
                node_id: nodeData.node_id,
                node_type: nodeData.node_type || 'unknown',
                duration_ms: nodeData.duration_ms || 0,
                token_usage: tokenUsage,
              });
            }
          }

          return {
            ...prevMetrics,
            total_token_usage: updatedTotalTokenUsage,
            node_breakdown: updatedNodeBreakdown,
          };
        });
      }
    }

    // Handle EXECUTION_COMPLETED to detect completion
    if (update.event_type === 'EXECUTION_COMPLETED') {
      setIsLive(false);

      // Refetch final metrics after execution completes
      setTimeout(() => {
        refetch();
      }, 1000);
    }
  }, [subscriptionData, refetch]);

  const handleRefetch = useCallback(() => {
    refetch();
  }, [refetch]);

  return {
    metrics,
    loading,
    error: error || null,
    refetch: handleRefetch,
    isLive,
  };
}
