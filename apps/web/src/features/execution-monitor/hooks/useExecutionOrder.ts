import { useState, useEffect, useCallback, useMemo } from 'react';
import { gql } from '@apollo/client';
import { ExecutionID, NodeID } from '@/core/types';
import { ExecutionStatus, isExecutionActive } from '@dipeo/domain-models';
import { createEntityQuery } from '@/graphql/hooks';

const EXECUTION_ORDER_QUERY = gql`
  query ExecutionOrder($executionId: ExecutionID!) {
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

// The executionOrder query returns data directly in the correct format
const transformExecutionData = (data: any): ExecutionOrderData => {
  // Handle case where data might be a string (JSONScalar)
  if (typeof data === 'string') {
    try {
      return JSON.parse(data);
    } catch (e) {
      console.error('Failed to parse executionOrder data:', e);
      return {
        executionId: '' as ExecutionID,
        status: 'error',
        nodes: [],
        totalNodes: 0,
      };
    }
  }
  
  // Data is already in the correct format
  return data;
};

// Create the query hook using the factory pattern
const useExecutionOrderQuery = createEntityQuery({
  entityName: 'Execution Order',
  document: EXECUTION_ORDER_QUERY,
  cacheStrategy: 'cache-and-network',
  silent: true, // We handle errors at the component level
});

export const useExecutionOrder = (executionId?: ExecutionID) => {
  const [executionOrder, setExecutionOrder] = useState<ExecutionOrderData | null>(null);
  
  // Determine if we should poll based on execution status
  const shouldPoll = executionOrder ? isExecutionActive(executionOrder.status as ExecutionStatus) : true;
  
  // Dynamic poll interval based on execution status
  const pollInterval = useMemo(() => {
    if (!executionId) return 0;
    return shouldPoll ? 2000 : 0;
  }, [executionId, shouldPoll]);
  
  const { data, loading, error, refetch } = useExecutionOrderQuery(
    { executionId },
    {
      skip: !executionId,
      pollInterval,
      onCompleted: (data) => {
        if (data?.executionOrder) {
          const transformedData = transformExecutionData(data.executionOrder);
          setExecutionOrder(transformedData);
        }
      },
    }
  );

  const refreshExecutionOrder = useCallback(async () => {
    if (executionId) {
      try {
        const result = await refetch({ executionId });
        if (result.data?.executionOrder) {
          const transformedData = transformExecutionData(result.data.executionOrder);
          setExecutionOrder(transformedData);
        }
      } catch (err) {
        // Error is handled by the query hook
        console.error('Failed to refresh execution order:', err);
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