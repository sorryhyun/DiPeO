import { StateCreator } from 'zustand';
import { NodeID } from '@/core/types';
import { UnifiedStore } from '@/core/store/unifiedStore.types';

export interface NodeState {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'paused';
  error?: string;
  timestamp: number;
  skipReason?: string;
}

export interface ExecutionState {
  id: string | null;
  isRunning: boolean;
  isPaused: boolean;
  runningNodes: Set<NodeID>;
  nodeStates: Map<NodeID, NodeState>;
  context: Record<string, unknown>;
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
  
  // Execution state queries
  isNodeRunning: (nodeId: NodeID) => boolean;
  getNodeExecutionState: (nodeId: NodeID) => NodeState | undefined;
  getExecutionProgress: () => { completed: number; total: number; percentage: number };
}

export const createExecutionSlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  ExecutionSlice
> = (set, get) => ({
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
    state.activeView = 'execution';
    state.executionReadOnly = true;
  }),
  
  stopExecution: () => set(state => {
    state.execution.isRunning = false;
    state.execution.isPaused = false;
    state.execution.runningNodes.clear();
    state.executionReadOnly = false;
  }),
  
  pauseExecution: () => set(state => {
    state.execution.isPaused = true;
    // Keep the execution state but pause all running nodes
    state.execution.runningNodes.forEach(nodeId => {
      const nodeState = state.execution.nodeStates.get(nodeId);
      if (nodeState && nodeState.status === 'running') {
        state.execution.nodeStates.set(nodeId, {
          ...nodeState,
          status: 'paused'
        });
      }
    });
  }),
  
  resumeExecution: () => set(state => {
    state.execution.isPaused = false;
    // Resume all paused nodes
    state.execution.nodeStates.forEach((nodeState, nodeId) => {
      if (nodeState.status === 'paused') {
        state.execution.nodeStates.set(nodeId, {
          ...nodeState,
          status: 'running'
        });
        state.execution.runningNodes.add(nodeId);
      }
    });
  }),
  
  // Node state management
  updateNodeExecution: (nodeId, nodeState) => set(state => {
    state.execution.nodeStates.set(nodeId, nodeState);
    
    if (nodeState.status === 'running') {
      state.execution.runningNodes.add(nodeId);
    } else {
      state.execution.runningNodes.delete(nodeId);
    }
  }),
  
  setNodeRunning: (nodeId) => set(state => {
    const nodeState: NodeState = {
      status: 'running',
      timestamp: Date.now()
    };
    state.execution.nodeStates.set(nodeId, nodeState);
    state.execution.runningNodes.add(nodeId);
  }),
  
  setNodeCompleted: (nodeId) => set(state => {
    const nodeState: NodeState = {
      status: 'completed',
      timestamp: Date.now()
    };
    state.execution.nodeStates.set(nodeId, nodeState);
    state.execution.runningNodes.delete(nodeId);
  }),
  
  setNodeFailed: (nodeId, error) => set(state => {
    const nodeState: NodeState = {
      status: 'failed',
      timestamp: Date.now(),
      error
    };
    state.execution.nodeStates.set(nodeId, nodeState);
    state.execution.runningNodes.delete(nodeId);
  }),
  
  setNodeSkipped: (nodeId, reason) => set(state => {
    const nodeState: NodeState = {
      status: 'skipped',
      timestamp: Date.now(),
      skipReason: reason
    };
    state.execution.nodeStates.set(nodeId, nodeState);
    state.execution.runningNodes.delete(nodeId);
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
  }),
  
  // Execution state queries
  isNodeRunning: (nodeId) => {
    const state = get();
    return state.execution.runningNodes.has(nodeId);
  },
  
  getNodeExecutionState: (nodeId) => {
    const state = get();
    return state.execution.nodeStates.get(nodeId);
  },
  
  getExecutionProgress: () => {
    const state = get();
    const total = state.nodes.size;
    const completed = Array.from(state.execution.nodeStates.values())
      .filter(nodeState => 
        nodeState.status === 'completed' || 
        nodeState.status === 'skipped' ||
        nodeState.status === 'failed'
      ).length;
    
    return {
      completed,
      total,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0
    };
  }
});