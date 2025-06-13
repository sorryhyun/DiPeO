import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { NodeID } from '@/types';
import type { NodeState } from '@/stores/slices/executionSlice';

interface ExecutionData {
  // Execution state
  executionId: string | null;
  isRunning: boolean;
  
  // Node states
  runningNodes: Set<NodeID>;
  nodeStates: Map<NodeID, NodeState>;
  
  // Context data
  context: Record<string, unknown>;
  
  // Computed values
  runningNodeCount: number;
  completedNodeCount: number;
  failedNodeCount: number;
  totalNodeCount: number;
  progress: number;
}

/**
 * Focused selector hook for execution data
 * Provides all execution-related state with computed values
 * 
 * @example
 * ```typescript
 * const { isRunning, runningNodes, progress } = useExecutionData();
 * ```
 */
export const useExecutionData = (): ExecutionData => {
  return useUnifiedStore(
    useShallow(state => {
      // Count node states
      const nodeStateArray = Array.from(state.execution.nodeStates.values());
      const completedNodeCount = nodeStateArray.filter(s => s.status === 'completed').length;
      const failedNodeCount = nodeStateArray.filter(s => s.status === 'failed').length;
      const totalNodeCount = state.nodes.size;
      
      return {
        executionId: state.execution.id,
        isRunning: state.execution.isRunning,
        runningNodes: state.execution.runningNodes,
        nodeStates: state.execution.nodeStates,
        context: state.execution.context,
        runningNodeCount: state.execution.runningNodes.size,
        completedNodeCount,
        failedNodeCount,
        totalNodeCount,
        progress: totalNodeCount > 0 
          ? Math.round(((completedNodeCount + failedNodeCount) / totalNodeCount) * 100) 
          : 0
      };
    })
  );
};

/**
 * Hook to check if a specific node is running
 */
export const useIsNodeRunning = (nodeId: NodeID): boolean => {
  return useUnifiedStore(state => state.execution.runningNodes.has(nodeId));
};

/**
 * Hook to get execution state for a specific node
 */
export const useNodeExecutionState = (nodeId: NodeID): NodeState | undefined => {
  return useUnifiedStore(state => state.execution.nodeStates.get(nodeId));
};

/**
 * Hook to get all running node IDs as array
 */
export const useRunningNodeIds = (): NodeID[] => {
  return useUnifiedStore(
    useShallow(state => Array.from(state.execution.runningNodes))
  );
};

/**
 * Hook to get execution context value by key
 */
export const useExecutionContextValue = <T = unknown>(key: string): T | undefined => {
  return useUnifiedStore(state => state.execution.context[key] as T | undefined);
};

/**
 * Hook to track if any execution is in progress
 */
export const useIsExecuting = (): boolean => {
  return useUnifiedStore(state => state.execution.isRunning);
};