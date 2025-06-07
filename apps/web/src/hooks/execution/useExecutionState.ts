/**
 * useExecutionState - Pure state machine for execution state management
 * 
 * This hook manages the core execution state without any WebSocket or UI concerns.
 * It provides a clean interface for tracking execution progress and node states.
 */

import { useState, useCallback } from 'react';

export interface ExecutionStateV2 {
  isRunning: boolean;
  executionId: string | null;
  totalNodes: number;
  completedNodes: number;
  currentNode: string | null;
  startTime: Date | null;
  endTime: Date | null;
  error: string | null;
}

export interface NodeStateV2 {
  status: 'pending' | 'running' | 'completed' | 'skipped' | 'error' | 'paused';
  startTime: Date | null;
  endTime: Date | null;
  progress?: string;
  error?: string;
  tokenCount?: number;
  skipReason?: string;
}

export interface UseExecutionStateReturn {
  // State
  executionState: ExecutionStateV2;
  nodeStates: Record<string, NodeStateV2>;
  
  // Actions
  startExecution: (executionId: string, totalNodes: number) => void;
  completeExecution: (totalTokens?: number) => void;
  errorExecution: (error: string) => void;
  abortExecution: () => void;
  
  // Node actions
  startNode: (nodeId: string) => void;
  updateNodeProgress: (nodeId: string, progress: string) => void;
  completeNode: (nodeId: string, tokenCount?: number) => void;
  skipNode: (nodeId: string, reason?: string) => void;
  errorNode: (nodeId: string, error: string) => void;
  pauseNode: (nodeId: string) => void;
  resumeNode: (nodeId: string) => void;
  
  // Utilities
  resetState: () => void;
  getNodeState: (nodeId: string) => NodeStateV2 | undefined;
  isNodeRunning: (nodeId: string) => boolean;
}

const initialExecutionState: ExecutionStateV2 = {
  isRunning: false,
  executionId: null,
  totalNodes: 0,
  completedNodes: 0,
  currentNode: null,
  startTime: null,
  endTime: null,
  error: null
};

const createDefaultNodeState = (): NodeStateV2 => ({
  status: 'pending',
  startTime: null,
  endTime: null,
  progress: undefined,
  error: undefined,
  tokenCount: undefined,
  skipReason: undefined
});

export function useExecutionState(): UseExecutionStateReturn {
  const [executionState, setExecutionState] = useState<ExecutionStateV2>(initialExecutionState);
  const [nodeStates, setNodeStates] = useState<Record<string, NodeStateV2>>({});

  // Execution actions
  const startExecution = useCallback((executionId: string, totalNodes: number) => {
    setExecutionState({
      isRunning: true,
      executionId,
      totalNodes,
      completedNodes: 0,
      currentNode: null,
      startTime: new Date(),
      endTime: null,
      error: null
    });
    setNodeStates({});
  }, []);

  const completeExecution = useCallback((_totalTokens?: number) => {
    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      currentNode: null,
      endTime: new Date(),
      error: null
    }));
  }, []);

  const errorExecution = useCallback((error: string) => {
    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      currentNode: null,
      endTime: new Date(),
      error
    }));
  }, []);

  const abortExecution = useCallback(() => {
    setExecutionState(prev => ({
      ...prev,
      isRunning: false,
      currentNode: null,
      endTime: new Date(),
      error: 'Execution aborted'
    }));
  }, []);

  // Node actions
  const startNode = useCallback((nodeId: string) => {
    setExecutionState(prev => ({
      ...prev,
      currentNode: nodeId
    }));
    setNodeStates(prev => ({
      ...prev,
      [nodeId]: {
        status: 'running',
        startTime: new Date(),
        endTime: null
      }
    }));
  }, []);

  const updateNodeProgress = useCallback((nodeId: string, progress: string) => {
    setNodeStates(prev => {
      const currentNode = prev[nodeId];
      if (!currentNode) return prev;
      
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          progress
        }
      };
    });
  }, []);

  const completeNode = useCallback((nodeId: string, tokenCount?: number) => {
    setExecutionState(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1,
      currentNode: prev.currentNode === nodeId ? null : prev.currentNode
    }));
    setNodeStates(prev => {
      const currentNode = prev[nodeId] || createDefaultNodeState();
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          status: 'completed' as const,
          endTime: new Date(),
          tokenCount
        }
      };
    });
  }, []);

  const skipNode = useCallback((nodeId: string, reason?: string) => {
    setExecutionState(prev => ({
      ...prev,
      completedNodes: prev.completedNodes + 1,
      currentNode: prev.currentNode === nodeId ? null : prev.currentNode
    }));
    setNodeStates(prev => {
      const currentNode = prev[nodeId] || createDefaultNodeState();
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          status: 'skipped' as const,
          endTime: new Date(),
          skipReason: reason
        }
      };
    });
  }, []);

  const errorNode = useCallback((nodeId: string, error: string) => {
    setNodeStates(prev => {
      const currentNode = prev[nodeId] || createDefaultNodeState();
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          status: 'error' as const,
          endTime: new Date(),
          error
        }
      };
    });
  }, []);

  const pauseNode = useCallback((nodeId: string) => {
    setNodeStates(prev => {
      const currentNode = prev[nodeId] || createDefaultNodeState();
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          status: 'paused' as const
        }
      };
    });
  }, []);

  const resumeNode = useCallback((nodeId: string) => {
    setNodeStates(prev => {
      const currentNode = prev[nodeId] || createDefaultNodeState();
      return {
        ...prev,
        [nodeId]: {
          ...currentNode,
          status: 'running' as const
        }
      };
    });
  }, []);

  // Utilities
  const resetState = useCallback(() => {
    setExecutionState(initialExecutionState);
    setNodeStates({});
  }, []);

  const getNodeState = useCallback((nodeId: string) => {
    return nodeStates[nodeId];
  }, [nodeStates]);

  const isNodeRunning = useCallback((nodeId: string) => {
    return nodeStates[nodeId]?.status === 'running';
  }, [nodeStates]);

  return {
    // State
    executionState,
    nodeStates,
    
    // Actions
    startExecution,
    completeExecution,
    errorExecution,
    abortExecution,
    
    // Node actions
    startNode,
    updateNodeProgress,
    completeNode,
    skipNode,
    errorNode,
    pauseNode,
    resumeNode,
    
    // Utilities
    resetState,
    getNodeState,
    isNodeRunning
  };
}