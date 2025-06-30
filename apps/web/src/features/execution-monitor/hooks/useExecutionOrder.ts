import { useState, useEffect, useCallback } from 'react';
import { gql, useQuery } from '@apollo/client';
import { ExecutionID, NodeID } from '@/core/types';
import { ExecutionStatus, isExecutionActive } from '@dipeo/domain-models';

// TODO: Implement executionOrder query in GraphQL schema
// For now, using execution query to get basic execution state
const EXECUTION_ORDER_QUERY = gql`
  query ExecutionOrder($executionId: ExecutionID!) {
    execution(id: $executionId) {
      id
      status
      startedAt
      endedAt
      nodeStates
      nodeOutputs
      tokenUsage {
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

export const useExecutionOrder = (executionId?: ExecutionID) => {
  const [executionOrder, setExecutionOrder] = useState<ExecutionOrderData | null>(null);
  
  // Determine if we should poll based on execution status
  const shouldPoll = executionOrder ? isExecutionActive(executionOrder.status as ExecutionStatus) : true;
  
  const { data, loading, error, refetch } = useQuery(EXECUTION_ORDER_QUERY, {
    variables: { executionId },
    skip: !executionId,
    pollInterval: shouldPoll ? 2000 : 0, // Poll only if execution is active
  });

  useEffect(() => {
    if (data?.execution) {
      // TODO: Parse nodeStates to build execution order
      // For now, create a minimal implementation
      const executionData: ExecutionOrderData = {
        executionId: executionId!,
        status: data.execution.status,
        startedAt: data.execution.startedAt,
        endedAt: data.execution.endedAt,
        nodes: [],
        totalNodes: 0,
      };
      
      // Parse nodeStates if available
      if (data.execution.nodeStates) {
        try {
          const nodeStates = typeof data.execution.nodeStates === 'string' 
            ? JSON.parse(data.execution.nodeStates) 
            : data.execution.nodeStates;
          
          executionData.nodes = Object.entries(nodeStates).map(([nodeId, state]: [string, any]) => ({
            nodeId: nodeId as NodeID,
            nodeName: state.nodeName || nodeId,
            status: state.status || 'pending',
            startedAt: state.startedAt,
            endedAt: state.endedAt,
            duration: state.duration,
            error: state.error,
          }));
          executionData.totalNodes = executionData.nodes.length;
        } catch (e) {
          console.error('Failed to parse nodeStates:', e);
        }
      }
      
      setExecutionOrder(executionData);
    }
  }, [data, executionId]);

  const refreshExecutionOrder = useCallback(async () => {
    if (executionId) {
      const result = await refetch({ executionId });
      if (result.data?.execution) {
        // Data will be processed by the useEffect above
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