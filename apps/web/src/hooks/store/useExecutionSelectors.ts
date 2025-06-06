import React from 'react';
import { useExecutionStore } from '@/stores/executionStore';

export const useExecutionSelectors = () => {
  const runContext = useExecutionStore(state => state.runContext);
  const runningNodes = useExecutionStore(state => state.runningNodes);
  const currentRunningNode = useExecutionStore(state => state.currentRunningNode);
  const nodeRunningStates = useExecutionStore(state => state.nodeRunningStates);
  const skippedNodes = useExecutionStore(state => state.skippedNodes);
  const lastUpdate = useExecutionStore(state => state.lastUpdate);
  
  // Actions
  const setRunContext = useExecutionStore(state => state.setRunContext);
  const addRunningNode = useExecutionStore(state => state.addRunningNode);
  const removeRunningNode = useExecutionStore(state => state.removeRunningNode);
  const setCurrentRunningNode = useExecutionStore(state => state.setCurrentRunningNode);
  const addSkippedNode = useExecutionStore(state => state.addSkippedNode);
  
  return React.useMemo(() => ({
    // State
    runContext,
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes,
    lastUpdate,
    
    // Actions
    setRunContext,
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    addSkippedNode,
    
    // Utility functions
    clearRunContext: () => setRunContext({}),
    clearRunningNodes: () => {
      runningNodes.forEach(nodeId => removeRunningNode(nodeId));
      setCurrentRunningNode(null);
    },
  }), [
    runContext, runningNodes, currentRunningNode, nodeRunningStates, skippedNodes, lastUpdate,
    setRunContext, addRunningNode, removeRunningNode, setCurrentRunningNode, addSkippedNode
  ]);
};

// Optimized hook for specific node execution state
export const useNodeExecutionState = (nodeId: string) => {
  const lastUpdate = useExecutionStore(state => state.lastUpdate);
  const runningNodes = useExecutionStore(state => state.runningNodes);
  const currentRunningNode = useExecutionStore(state => state.currentRunningNode);
  const nodeRunningState = useExecutionStore(state => state.nodeRunningStates[nodeId] || false);
  const skippedNodeInfo = useExecutionStore(state => state.skippedNodes[nodeId]);
  
  const isRunning = runningNodes.includes(nodeId);
  const isCurrentRunning = currentRunningNode === nodeId;
  const isSkipped = Boolean(skippedNodeInfo);
  
  // Debug logging for node execution state
  React.useEffect(() => {
    if (isRunning || nodeRunningState || isSkipped) {
      console.log(`[useNodeExecutionState] Node ${nodeId} state:`, {
        nodeId,
        isRunning,
        isCurrentRunning,
        nodeRunningState,
        isSkipped,
        skipReason: skippedNodeInfo?.reason,
        runningNodes,
        lastUpdate
      });
    }
  }, [nodeId, isRunning, isCurrentRunning, nodeRunningState, isSkipped, skippedNodeInfo, runningNodes, lastUpdate]);
  
  return React.useMemo(() => ({
    isRunning,
    isCurrentRunning,
    nodeRunningState,
    isSkipped,
    skipReason: skippedNodeInfo?.reason,
  }), [isRunning, isCurrentRunning, nodeRunningState, isSkipped, skippedNodeInfo?.reason, lastUpdate]);
};