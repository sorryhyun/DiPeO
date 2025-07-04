import { useState, useEffect, useCallback, useMemo } from 'react';
import { gql } from '@apollo/client';
import { ExecutionID, NodeID } from '@/core/types';
import { ExecutionStatus, isExecutionActive } from '@dipeo/domain-models';
import { createEntityQuery } from '@/graphql/hooks';

// TODO: Implement executionOrder query in GraphQL schema
// For now, using execution query to get basic execution state
const EXECUTION_ORDER_QUERY = gql`
  query ExecutionOrder($executionId: ExecutionID!) {
    execution(id: $executionId) {
      id
      status
      started_at
      ended_at
      node_states
      node_outputs
      token_usage {
        input
        output
        cached
        total
      }
    }
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

// Transform raw execution data to ExecutionOrderData
const transformExecutionData = (
  execution: any,
  executionId: ExecutionID
): ExecutionOrderData => {
  const executionData: ExecutionOrderData = {
    executionId,
    status: execution.status,
    startedAt: execution.started_at,
    endedAt: execution.ended_at,
    nodes: [],
    totalNodes: 0,
  };
  
  // Parse nodeStates if available
  if (execution.node_states) {
    try {
      const nodeStates = typeof execution.node_states === 'string' 
        ? JSON.parse(execution.node_states) 
        : execution.node_states;
      
      executionData.nodes = Object.entries(nodeStates).map(([nodeId, state]: [string, any]) => ({
        nodeId: nodeId as NodeID,
        nodeName: state.nodeName || nodeId,
        status: state.status || 'pending',
        startedAt: state.startedAt,
        endedAt: state.endedAt,
        duration: state.duration,
        error: state.error,
        tokenUsage: state.tokenUsage,
      }));
      executionData.totalNodes = executionData.nodes.length;
    } catch (e) {
      console.error('Failed to parse nodeStates:', e);
    }
  }
  
  return executionData;
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
        if (data?.execution && executionId) {
          const transformedData = transformExecutionData(data.execution, executionId);
          setExecutionOrder(transformedData);
        }
      },
    }
  );

  const refreshExecutionOrder = useCallback(async () => {
    if (executionId) {
      try {
        const result = await refetch({ executionId });
        if (result.data?.execution) {
          const transformedData = transformExecutionData(result.data.execution, executionId);
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