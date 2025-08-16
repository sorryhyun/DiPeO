import { useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

const LIST_ACTIVE_EXECUTIONS = gql`
  query ListActiveExecutions($filter: ExecutionFilterInput, $limit: Int) {
    executions(filter: $filter, limit: $limit) {
      id
      status
      diagram_id
      started_at
      ended_at
    }
  }
`;

interface UseAutoFetchExecutionsOptions {
  enabled: boolean;
  onExecutionsFetched: (ids: string[]) => void;
  includeCompleted?: boolean;
  limit?: number;
}

/**
 * Hook to automatically fetch and monitor active executions
 * Used when ?monitor=true is provided without specific execution IDs
 */
export function useAutoFetchExecutions({
  enabled,
  onExecutionsFetched,
  includeCompleted = false,
  limit = 50,
}: UseAutoFetchExecutionsOptions) {
  const { data, loading, error } = useQuery(LIST_ACTIVE_EXECUTIONS, {
    variables: {
      filter: includeCompleted ? undefined : { status: 'RUNNING' },
      limit,
    },
    skip: !enabled,
    pollInterval: enabled ? 3000 : 0, // Poll every 3 seconds when enabled
    fetchPolicy: 'network-only', // Always fetch fresh data
  });

  useEffect(() => {
    if (!enabled || loading || error) return;
    
    if (data?.executions) {
      // Filter to get relevant executions
      const relevantExecutions = data.executions.filter((exec: any) => {
        // IMPORTANT: Exclude batch executions (sub-executions created by PersonBatchJobNode)
        // These have IDs like "exec_XXX_batch_0", "exec_XXX_batch_1", etc.
        if (exec.id && exec.id.includes('_batch_')) {
          return false;
        }
        
        // Include running executions always
        if (exec.status === 'RUNNING' || exec.status === 'PENDING') return true;
        
        // Include recently completed executions if requested (within last 5 minutes)
        if (includeCompleted && exec.status === 'COMPLETED') {
          const endedAt = new Date(exec.ended_at);
          const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
          return endedAt > fiveMinutesAgo;
        }
        
        // Include recent failures (within last 10 minutes)
        if (exec.status === 'FAILED' && exec.ended_at) {
          const endedAt = new Date(exec.ended_at);
          const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
          return endedAt > tenMinutesAgo;
        }
        
        return false;
      }) as Array<{ id: string }>;
      
      // Deduplicate IDs in case the backend returns duplicates
      const ids = [...new Set(relevantExecutions.map(e => e.id))];
      onExecutionsFetched(ids);
    }
  }, [data, enabled, loading, error, onExecutionsFetched, includeCompleted]);
  
  return { loading, error, executionCount: data?.executions?.length || 0 };
}