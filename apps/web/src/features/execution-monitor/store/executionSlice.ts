import {StateCreator} from 'zustand';
import {NodeID, executionId, diagramId} from '@/core/types';
import {UnifiedStore} from '@/core/store/unifiedStore.types';
import {
  type DiagramID,
  type ExecutionID,
  type ExecutionState as CanonicalExecutionState,
  ExecutionStatus,
  NodeExecutionStatus,
  type NodeState as DomainNodeState,
} from '@dipeo/domain-models';

/**
 * Store-specific node state that tracks execution state of individual nodes.
 * This is a simplified version of NodeResult for store usage.
 */
export interface NodeState {
  status: NodeExecutionStatus;
  error?: string;
  timestamp: number; // Using number for performance in store
  skipReason?: string;
}

/**
 * Store-specific execution state optimized for Zustand.
 * Uses Set/Map for efficient updates and lookups.
 */
export interface ExecutionState {
  id: string | null;
  isRunning: boolean;
  isPaused: boolean;
  runningNodes: Set<NodeID>;
  nodeStates: Map<NodeID, NodeState>;
  context: Record<string, unknown>;
}

/**
 * Convert store NodeState to domain NodeState
 */
export function toDomainNodeState(nodeState: NodeState): DomainNodeState {
  return {
    status: nodeState.status,
    started_at: new Date(nodeState.timestamp).toISOString(),
    ended_at: null,
    error: nodeState.error || null,
    token_usage: null,
  };
}

/**
 * Convert store ExecutionState to canonical ExecutionState
 */
export function toCanonicalExecutionState(
  storeState: ExecutionState,
  diagramIdParam?: string | null,
): CanonicalExecutionState {
  let status: ExecutionStatus;
  if (storeState.isPaused) {
    status = ExecutionStatus.PAUSED;
  } else if (storeState.isRunning) {
    status = ExecutionStatus.RUNNING;
  } else {
    // Check if any nodes failed
    const hasFailed = Array.from(storeState.nodeStates.values()).some(
      state => state.status === NodeExecutionStatus.FAILED
    );
    status = hasFailed ? ExecutionStatus.FAILED : ExecutionStatus.COMPLETED;
  }
  
  // Convert Map to dictionary for nodeStates
  const nodeStatesDict: Record<string, DomainNodeState> = {};
  storeState.nodeStates.forEach((nodeState, nodeId) => {
    nodeStatesDict[nodeId] = {
      status: nodeState.status,
      started_at: new Date(nodeState.timestamp).toISOString(),
      ended_at: nodeState.status !== NodeExecutionStatus.RUNNING ? new Date(nodeState.timestamp).toISOString() : null,
      error: nodeState.error || null,
      token_usage: null,
    };
  });
  
  // Convert context to nodeOutputs as plain objects
  const nodeOutputsDict: Record<string, Record<string, any>> = {};
  Object.entries(storeState.context).forEach(([nodeId, value]) => {
    nodeOutputsDict[nodeId] = value as Record<string, any>;
  });
  
  return {
    id: storeState.id ? executionId(storeState.id) : executionId(''),
    status,
    diagram_id: diagramIdParam ? diagramId(diagramIdParam) : null,
    started_at: new Date().toISOString(), // Store doesn't track this, using current time
    node_states: nodeStatesDict,
    node_outputs: nodeOutputsDict,
    variables: {},
    token_usage: { input: 0, output: 0, cached: null, total: 0 },
    error: null,
    ended_at: status === ExecutionStatus.COMPLETED || status === ExecutionStatus.FAILED ? new Date().toISOString() : null,
    is_active: storeState.isRunning,
    exec_counts: {},
    executed_nodes: [],
  };
}

export interface ExecutionSlice {
  execution: ExecutionState;
  
  // Execution control
  startExecution: (executionId: string) => void;
  stopExecution: () => void;
  pauseExecution: () => void;
  resumeExecution: () => void;
  
  // Node state management
  updateNodeExecution: (nodeId: NodeID, state: NodeState) => void;
  setNodeRunning: (nodeId: NodeID) => void;
  setNodeCompleted: (nodeId: NodeID) => void;
  setNodeFailed: (nodeId: NodeID, error: string) => void;
  setNodeSkipped: (nodeId: NodeID, reason: string) => void;
  
  // Context management
  updateExecutionContext: (updates: Record<string, unknown>) => void;
  clearExecutionContext: () => void;
}

// Helper to clear node from running state
const clearRunningNode = (state: UnifiedStore, nodeId: NodeID) => {
  state.execution.runningNodes.delete(nodeId);
};

// Helper to update node state
const updateNodeState = (state: UnifiedStore, nodeId: NodeID, nodeState: NodeState) => {
  state.execution.nodeStates.set(nodeId, nodeState);
  
  if (nodeState.status === NodeExecutionStatus.RUNNING) {
    state.execution.runningNodes.add(nodeId);
  } else {
    clearRunningNode(state, nodeId);
  }
};

export const createExecutionSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  ExecutionSlice
> = (set, _get) => ({
  execution: {
    id: null,
    isRunning: false,
    isPaused: false,
    runningNodes: new Set(),
    nodeStates: new Map(),
    context: {}
  },
  
  // Execution control
  startExecution: (executionId) => set(state => {
    state.execution = {
      id: executionId,
      isRunning: true,
      isPaused: false,
      runningNodes: new Set(),
      nodeStates: new Map(),
      context: {}
    };
    // NOTE: UI state changes should be handled by UI slice listening to execution state changes
    // This maintains proper slice isolation
  }),
  
  stopExecution: () => set(state => {
    state.execution.isRunning = false;
    state.execution.isPaused = false;
    state.execution.runningNodes.clear();
    state.execution.nodeStates.clear(); // Clear all node highlights
    // NOTE: UI state changes should be handled by UI slice listening to execution state changes
  }),
  
  pauseExecution: () => set(state => {
    state.execution.isPaused = true;
    // Keep the execution state but pause all running nodes
    state.execution.runningNodes.forEach(nodeId => {
      const nodeState = state.execution.nodeStates.get(nodeId);
      if (nodeState && nodeState.status === NodeExecutionStatus.RUNNING) {
        state.execution.nodeStates.set(nodeId, {
          ...nodeState,
          status: NodeExecutionStatus.PAUSED
        });
      }
    });
  }),
  
  resumeExecution: () => set(state => {
    state.execution.isPaused = false;
    // Resume all paused nodes
    state.execution.nodeStates.forEach((nodeState, nodeId) => {
      if (nodeState.status === NodeExecutionStatus.PAUSED) {
        state.execution.nodeStates.set(nodeId, {
          ...nodeState,
          status: NodeExecutionStatus.RUNNING
        });
        state.execution.runningNodes.add(nodeId);
      }
    });
  }),
  
  // Node state management
  updateNodeExecution: (nodeId, nodeState) => set(state => {
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeRunning: (nodeId) => set(state => {
    const nodeState: NodeState = {
      status: NodeExecutionStatus.RUNNING,
      timestamp: Date.now()
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeCompleted: (nodeId) => set(state => {
    const nodeState: NodeState = {
      status: NodeExecutionStatus.COMPLETED,
      timestamp: Date.now()
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeFailed: (nodeId, error) => set(state => {
    const nodeState: NodeState = {
      status: NodeExecutionStatus.FAILED,
      timestamp: Date.now(),
      error
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeSkipped: (nodeId, reason) => set(state => {
    const nodeState: NodeState = {
      status: NodeExecutionStatus.SKIPPED,
      timestamp: Date.now(),
      skipReason: reason
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  // Context management
  updateExecutionContext: (updates) => set(state => {
    state.execution.context = {
      ...state.execution.context,
      ...updates
    };
  }),
  
  clearExecutionContext: () => set(state => {
    state.execution.context = {};
  })
});