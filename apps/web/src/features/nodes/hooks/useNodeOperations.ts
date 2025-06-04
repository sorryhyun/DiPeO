import React from 'react';
import { useDiagramStore } from '@/state/stores';
import { useExecutionStore } from '@/state/stores/executionStore';

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
  return useDiagramStore(state => state.updateNodeData);
};

// Node operations
export const useNodes = () => {
  const nodes = useDiagramStore(state => state.nodes);
  const onNodesChange = useDiagramStore(state => state.onNodesChange);
  const addNode = useDiagramStore(state => state.addNode);
  const deleteNode = useDiagramStore(state => state.deleteNode);
  
  return {
    nodes,
    onNodesChange,
    addNode,
    deleteNode,
  };
};