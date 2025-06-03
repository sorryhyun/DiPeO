import React from 'react';
import { useNodeArrowStore } from '@/global/stores';
import { useExecutionStore } from '@/global/stores/executionStore';

// ===== Node-Specific Hooks =====

// Execution state for specific node - avoids subscribing to entire execution store
export const useNodeExecutionState = (nodeId: string) => {
  const isRunning = useExecutionStore(state => state.runningNodes.includes(nodeId));
  const isCurrentRunning = useExecutionStore(state => state.currentRunningNode === nodeId);
  const nodeRunningState = useExecutionStore(state => state.nodeRunningStates[nodeId] || false);
  
  // Memoize the return object to prevent unnecessary re-renders
  return React.useMemo(() => ({
    isRunning,
    isCurrentRunning,
    nodeRunningState,
  }), [isRunning, isCurrentRunning, nodeRunningState]);
};

// Single function selectors for common operations to avoid re-renders
export const useNodeDataUpdater = () => {
  return useNodeArrowStore(state => state.updateNodeData);
};

// Node operations
export const useNodes = () => {
  const nodes = useNodeArrowStore(state => state.nodes);
  const onNodesChange = useNodeArrowStore(state => state.onNodesChange);
  const addNode = useNodeArrowStore(state => state.addNode);
  const deleteNode = useNodeArrowStore(state => state.deleteNode);
  
  return {
    nodes,
    onNodesChange,
    addNode,
    deleteNode,
  };
};