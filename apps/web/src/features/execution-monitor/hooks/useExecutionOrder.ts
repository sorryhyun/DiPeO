import { useState, useEffect, useCallback } from 'react';
import { gql, useQuery } from '@apollo/client';
import { ExecutionID, NodeID } from '@/core/types';

const EXECUTION_ORDER_QUERY = gql`
  query ExecutionOrder($executionId: ID!) {
    executionOrder(executionId: $executionId)
  }
`;

export interface ExecutionStep {
  nodeId: NodeID;
  nodeName: string;
  status: string; // Backend returns string status values
  startedAt?: string;
  endedAt?: string;
  duration?: number;
  error?: string;
  tokenUsage?: {
    input: number;
    output: number;
    cached?: number;
    total: number;
  };
}

export interface ExecutionOrderData {
  executionId: ExecutionID;
  status: string;
  startedAt?: string;
  endedAt?: string;
  nodes: ExecutionStep[];
  totalNodes: number;
}

export const useExecutionOrder = (executionId?: ExecutionID) => {
  const [executionOrder, setExecutionOrder] = useState<ExecutionOrderData | null>(null);
  
  const { data, loading, error, refetch } = useQuery(EXECUTION_ORDER_QUERY, {
    variables: { executionId },
    skip: !executionId,
    pollInterval: 2000, // Poll every 2 seconds for live updates
  });

  useEffect(() => {
    if (data?.executionOrder) {
      setExecutionOrder(data.executionOrder);
    }
  }, [data]);

  const refreshExecutionOrder = useCallback(async () => {
    if (executionId) {
      const result = await refetch({ executionId });
      if (result.data?.executionOrder) {
        setExecutionOrder(result.data.executionOrder);
      }
    }
  }, [executionId, refetch]);

  return {
    executionOrder,
    loading,
    error,
    refreshExecutionOrder,
  };
};