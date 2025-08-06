import React, { useState, useEffect, useMemo } from 'react';
import { Activity, Clock, CheckCircle, XCircle, AlertCircle, Play, Pause, RefreshCw } from 'lucide-react';
import { useExecution } from '@/hooks';
import { NodeExecutionStatus } from '@/domain/execution/types/execution';
import { ExecutionID, executionId } from '@/infrastructure/types';
import { Button } from '@/ui/components/common/forms/buttons';
import { useExecutionOrderQuery, ExecutionOrderQuery } from '@/__generated__/graphql';
import { ExecutionStatus, isExecutionActive } from '@dipeo/models';

interface ExecutionStep {
  nodeId: string;
  nodeName: string;
  status: string;
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

interface ExecutionOrderData {
  executionId: ExecutionID;
  status: string;
  startedAt?: string;
  endedAt?: string;
  nodes: ExecutionStep[];
  totalNodes: number;
}

interface ExecutionOrderViewProps {
  executionId?: ExecutionID;
}

export const ExecutionOrderView: React.FC<ExecutionOrderViewProps> = ({ executionId: providedExecutionId }) => {
  const { execution } = useExecution();
  const currentExecutionId = providedExecutionId || (execution?.id ? executionId(execution.id) : undefined);
  const [executionOrder, setExecutionOrder] = useState<ExecutionOrderData | null>(null);
  
  // Determine if we should poll based on execution status
  const shouldPoll = executionOrder ? isExecutionActive(executionOrder.status as ExecutionStatus) : true;
  
  // Dynamic poll interval based on execution status
  const pollInterval = useMemo(() => {
    if (!currentExecutionId) return 0;
    return shouldPoll ? 2000 : 0;
  }, [currentExecutionId, shouldPoll]);
  
  const { data, loading, error, refetch } = useExecutionOrderQuery({
    variables: { executionId: currentExecutionId! },
    skip: !currentExecutionId,
    pollInterval,
    onCompleted: (data: ExecutionOrderQuery) => {
      if (data?.execution_order) {
        // Handle case where data might be a string (JSONScalar)
        const parsedData = typeof data.execution_order === 'string' 
          ? JSON.parse(data.execution_order)
          : data.execution_order;
        setExecutionOrder(parsedData);
      }
    },
  });
  
  const refreshExecutionOrder = async () => {
    if (currentExecutionId) {
      await refetch({ executionId: currentExecutionId });
    }
  };

  const getStatusIcon = (status: NodeExecutionStatus) => {
    switch (status) {
      case NodeExecutionStatus.COMPLETED:
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case NodeExecutionStatus.FAILED:
        return <XCircle className="h-5 w-5 text-red-500" />;
      case NodeExecutionStatus.RUNNING:
        return <Activity className="h-5 w-5 text-blue-500 animate-pulse" />;
      case NodeExecutionStatus.PAUSED:
        return <Pause className="h-5 w-5 text-yellow-500" />;
      case NodeExecutionStatus.SKIPPED:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
      case NodeExecutionStatus.MAXITER_REACHED:
        return <RefreshCw className="h-5 w-5 text-orange-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: NodeExecutionStatus) => {
    switch (status) {
      case NodeExecutionStatus.COMPLETED:
        return 'bg-green-50 border-green-200';
      case NodeExecutionStatus.FAILED:
        return 'bg-red-50 border-red-200';
      case NodeExecutionStatus.RUNNING:
        return 'bg-blue-50 border-blue-200';
      case NodeExecutionStatus.PAUSED:
        return 'bg-yellow-50 border-yellow-200';
      case NodeExecutionStatus.SKIPPED:
        return 'bg-gray-50 border-gray-200';
      case NodeExecutionStatus.MAXITER_REACHED:
        return 'bg-orange-50 border-orange-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Activity className="h-12 w-12 mx-auto mb-2 opacity-50 animate-spin" />
          <p>Loading execution order...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center text-red-400">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>Error loading execution order</p>
          <p className="text-sm mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!currentExecutionId || !executionOrder) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No execution is currently running</p>
          <p className="text-sm mt-2">Start an execution to see the order of node executions</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-sm text-gray-700">Execution Order</h3>
          <div className="flex items-center space-x-4 text-xs text-gray-600">
            <span className="flex items-center">
              <Play className="h-3 w-3 mr-1" />
              {executionOrder.totalNodes} nodes executed
            </span>
            {executionOrder.status === 'RUNNING' && (
              <span className="flex items-center text-blue-600">
                <Activity className="h-3 w-3 mr-1 animate-pulse" />
                Running
              </span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={refreshExecutionOrder}
              title="Refresh execution order"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>

      {/* Execution Steps */}
      <div className="flex-1 overflow-y-auto px-4 py-2">
        {executionOrder.nodes.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>No nodes have been executed yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {executionOrder.nodes.map((step, index) => (
              <div
                key={step.nodeId}
                className={`rounded-lg border p-3 transition-all ${getStatusColor(step.status as NodeExecutionStatus)}`}
              >
                <div className="flex items-start space-x-3">
                  {/* Step Number */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>

                  {/* Step Details */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(step.status as NodeExecutionStatus)}
                        <span className="font-medium text-gray-900">{step.nodeName}</span>
                      </div>
                      {step.duration && (
                        <span className="text-xs text-gray-500">
                          {formatDuration(step.duration)}
                        </span>
                      )}
                    </div>
                    
                    {/* Timestamps */}
                    <div className="mt-1 text-xs text-gray-500">
                      {step.startedAt && (
                        <span>Started: {formatTimestamp(step.startedAt)}</span>
                      )}
                      {step.endedAt && (
                        <span className="ml-4">Ended: {formatTimestamp(step.endedAt)}</span>
                      )}
                    </div>

                    {/* Token Usage */}
                    {step.tokenUsage && step.tokenUsage.total > 0 && (
                      <div className="mt-1 text-xs text-gray-500">
                        Tokens: {step.tokenUsage.total} (in: {step.tokenUsage.input}, out: {step.tokenUsage.output})
                      </div>
                    )}

                    {/* Error Message */}
                    {step.error && (
                      <div className="mt-2 text-xs text-red-600 bg-red-100 rounded p-2">
                        {step.error}
                      </div>
                    )}
                  </div>
                </div>

                {/* Connection Line */}
                {index < executionOrder.nodes.length - 1 && (
                  <div className="ml-4 mt-2 border-l-2 border-gray-300 h-4" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};