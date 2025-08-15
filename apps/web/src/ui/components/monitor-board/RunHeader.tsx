import React, { useMemo } from 'react';
import { useStore } from 'zustand';
import { Pause, Play, X, Square, Activity, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import type { StoreApi } from 'zustand';
import type { ExecutionLocalStore } from './executionLocalStore';
import { useControlExecutionMutation } from '@/__generated__/graphql';

interface RunHeaderProps {
  executionId: string;
  store: StoreApi<ExecutionLocalStore>;
  onRemove?: () => void;
}

export function RunHeader({ executionId, store, onRemove }: RunHeaderProps) {
  const { 
    isRunning, 
    diagramName, 
    startedAt, 
    finishedAt,
    runningNodes,
    nodeStates 
  } = useStore(store);
  
  const [controlExecution] = useControlExecutionMutation();

  // Calculate elapsed time
  const elapsedTime = useMemo(() => {
    if (!startedAt) return '0s';
    const endTime = finishedAt || Date.now();
    const seconds = Math.floor((endTime - startedAt) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }, [startedAt, finishedAt]);

  // Calculate node stats
  const nodeStats = useMemo(() => {
    const stats = {
      completed: 0,
      failed: 0,
      running: runningNodes.size,
      total: nodeStates.size,
    };
    
    nodeStates.forEach((state) => {
      if (state.status === 'completed') stats.completed++;
      else if (state.status === 'failed') stats.failed++;
    });
    
    return stats;
  }, [runningNodes, nodeStates]);

  // Determine overall status
  const status = useMemo(() => {
    if (isRunning) return 'running';
    if (finishedAt) {
      if (nodeStats.failed > 0) return 'failed';
      return 'completed';
    }
    return 'pending';
  }, [isRunning, finishedAt, nodeStats.failed]);

  const handlePause = async () => {
    try {
      await controlExecution({
        variables: {
          input: {
            execution_id: executionId,
            action: 'pause',
          }
        },
      });
    } catch (error) {
      console.error('Failed to pause execution:', error);
    }
  };

  const handleResume = async () => {
    try {
      await controlExecution({
        variables: {
          input: {
            execution_id: executionId,
            action: 'resume',
          }
        },
      });
    } catch (error) {
      console.error('Failed to resume execution:', error);
    }
  };

  const handleAbort = async () => {
    try {
      await controlExecution({
        variables: {
          input: {
            execution_id: executionId,
            action: 'abort',
          }
        },
      });
    } catch (error) {
      console.error('Failed to abort execution:', error);
    }
  };

  return (
    <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-700">
      {/* Left side - Status and name */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {/* Status indicator */}
        <div className="flex-shrink-0">
          {status === 'running' && (
            <Activity className="w-5 h-5 text-blue-400 animate-pulse" />
          )}
          {status === 'completed' && (
            <CheckCircle2 className="w-5 h-5 text-green-400" />
          )}
          {status === 'failed' && (
            <XCircle className="w-5 h-5 text-red-400" />
          )}
          {status === 'pending' && (
            <AlertCircle className="w-5 h-5 text-gray-400" />
          )}
        </div>
        
        {/* Diagram name and execution ID */}
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-gray-200 truncate">
            {diagramName || 'Unnamed Diagram'}
          </div>
          <div className="text-xs text-gray-500 truncate">
            {executionId.slice(0, 8)}
          </div>
        </div>
      </div>

      {/* Middle - Stats */}
      <div className="flex items-center gap-4 px-3">
        {/* Elapsed time */}
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock className="w-3 h-3" />
          <span>{elapsedTime}</span>
        </div>
        
        {/* Node counters */}
        <div className="flex items-center gap-2 text-xs">
          {nodeStats.running > 0 && (
            <span className="text-blue-400">
              {nodeStats.running} running
            </span>
          )}
          {nodeStats.completed > 0 && (
            <span className="text-green-400">
              {nodeStats.completed} done
            </span>
          )}
          {nodeStats.failed > 0 && (
            <span className="text-red-400">
              {nodeStats.failed} failed
            </span>
          )}
        </div>
      </div>

      {/* Right side - Controls */}
      <div className="flex items-center gap-1 flex-shrink-0">
        {isRunning && (
          <>
            <button
              onClick={handlePause}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Pause execution"
            >
              <Pause className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={handleAbort}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Abort execution"
            >
              <Square className="w-4 h-4 text-gray-400" />
            </button>
          </>
        )}
        
        {!isRunning && status === 'running' && (
          <button
            onClick={handleResume}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title="Resume execution"
          >
            <Play className="w-4 h-4 text-gray-400" />
          </button>
        )}
        
        {onRemove && (
          <button
            onClick={onRemove}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors ml-1"
            title="Remove from board"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}
      </div>
    </div>
  );
}