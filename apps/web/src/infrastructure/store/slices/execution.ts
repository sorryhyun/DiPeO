import {NodeID} from '@/infrastructure/types';
import {
  type DiagramID,
  type ExecutionID,
  type ExecutionState as CanonicalExecutionState,
  Status,
  type NodeState as DomainNodeState,
  EventType,
  type ExecutionUpdate,
} from '@dipeo/models';
import { ExecutionConverter, type StoreNodeState, type StoreExecutionState } from '@/infrastructure/converters';
import type { UnifiedStore } from '../types';

// Re-export store types from converter
export type { StoreNodeState as NodeState, StoreExecutionState as ExecutionState } from '@/infrastructure/converters';

/**
 * Convert store NodeState to domain NodeState
 */
export function toDomainNodeState(nodeState: StoreNodeState): DomainNodeState {
  return {
    status: nodeState.status,
    started_at: new Date(nodeState.timestamp).toISOString(),
    ended_at: null,
    error: nodeState.error || null,
    llm_usage: null,
  };
}

/**
 * Convert store ExecutionState to canonical ExecutionState
 */
export function toCanonicalExecutionState(
  storeState: StoreExecutionState,
  diagramId?: string | null,
): CanonicalExecutionState {
  return ExecutionConverter.fromStore(
    storeState,
    diagramId ? diagramId as DiagramID : undefined
  );
}

export interface ExecutionSlice {
  execution: StoreExecutionState;
  
  // Execution control
  startExecution: (executionId: string) => void;
  stopExecution: () => void;
  pauseExecution: () => void;
  resumeExecution: () => void;
  clearExecutionState: () => void;
  
  // Node state management
  updateNodeExecution: (nodeId: NodeID, state: StoreNodeState) => void;
  setNodeRunning: (nodeId: NodeID) => void;
  setNodeCompleted: (nodeId: NodeID) => void;
  setNodeFailed: (nodeId: NodeID, error: string) => void;
  setNodeSkipped: (nodeId: NodeID, reason: string) => void;
  
  // Context management
  updateExecutionContext: (updates: Record<string, unknown>) => void;
  clearExecutionContext: () => void;
  
  // Event handling
  handleExecutionEvent: (event: ExecutionUpdate) => void;
}

// Helper to clear node from running state
const clearRunningNode = (state: UnifiedStore, nodeId: NodeID) => {
  state.execution.runningNodes.delete(nodeId);
};

// Helper to update node state
const updateNodeState = (state: UnifiedStore, nodeId: NodeID, nodeState: StoreNodeState) => {
  state.execution.nodeStates.set(nodeId, nodeState);
  
  if (nodeState.status === Status.RUNNING) {
    state.execution.runningNodes.add(nodeId);
  } else {
    clearRunningNode(state, nodeId);
  }
};

export const createExecutionSlice = (
  set: (fn: (state: UnifiedStore) => void) => void,
  _get: () => UnifiedStore,
  _api: any
): ExecutionSlice => ({
  execution: {
    id: null,
    isRunning: false,
    isPaused: false,
    runningNodes: new Set(),
    nodeStates: new Map(),
    context: {}
  },
  
  // Execution control
  startExecution: (executionId) => set((state: UnifiedStore) => {
    // Clear previous execution state before starting new one
    state.execution.nodeStates.clear();
    state.execution.runningNodes.clear();
    state.execution.context = {};
    
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
  
  stopExecution: () => set((state: UnifiedStore) => {
    state.execution.isRunning = false;
    state.execution.isPaused = false;
    state.execution.runningNodes.clear();
    // Do NOT clear nodeStates - preserve them for visualization
    // state.execution.nodeStates.clear(); // Clear all node highlights
    // NOTE: UI state changes should be handled by UI slice listening to execution state changes
  }),
  
  pauseExecution: () => set((state: UnifiedStore) => {
    state.execution.isPaused = true;
    // Keep the execution state but pause all running nodes
    state.execution.runningNodes.forEach(nodeId => {
      const nodeState = state.execution.nodeStates.get(nodeId);
      if (nodeState && nodeState.status === Status.RUNNING) {
        state.execution.nodeStates.set(nodeId, {
          ...nodeState,
          status: Status.PAUSED
        });
      }
    });
  }),
  
  resumeExecution: () => set((state: UnifiedStore) => {
    state.execution.isPaused = false;
    // Resume all paused nodes
    state.execution.nodeStates.forEach((nodeState, nodeId) => {
      if (nodeState.status === Status.PAUSED) {
        state.execution.nodeStates.set(nodeId, {
          ...nodeState,
          status: Status.RUNNING
        });
        state.execution.runningNodes.add(nodeId);
      }
    });
  }),
  
  // Node state management
  updateNodeExecution: (nodeId, nodeState) => set((state: UnifiedStore) => {
    console.log('[ExecutionSlice] Updating node execution:', nodeId, nodeState);
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeRunning: (nodeId) => set((state: UnifiedStore) => {
    const nodeState: StoreNodeState = {
      status: Status.RUNNING,
      timestamp: Date.now()
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeCompleted: (nodeId) => set((state: UnifiedStore) => {
    const nodeState: StoreNodeState = {
      status: Status.COMPLETED,
      timestamp: Date.now()
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeFailed: (nodeId, error) => set((state: UnifiedStore) => {
    const nodeState: StoreNodeState = {
      status: Status.FAILED,
      timestamp: Date.now(),
      error
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  setNodeSkipped: (nodeId, reason) => set((state: UnifiedStore) => {
    const nodeState: StoreNodeState = {
      status: Status.SKIPPED,
      timestamp: Date.now(),
      skipReason: reason
    };
    updateNodeState(state, nodeId, nodeState);
  }),
  
  // Context management
  updateExecutionContext: (updates) => set((state: UnifiedStore) => {
    state.execution.context = {
      ...state.execution.context,
      ...updates
    };
  }),
  
  clearExecutionContext: () => set((state: UnifiedStore) => {
    state.execution.context = {};
  }),
  
  clearExecutionState: () => set((state: UnifiedStore) => {
    state.execution = {
      id: null,
      isRunning: false,
      isPaused: false,
      runningNodes: new Set(),
      nodeStates: new Map(),
      context: {}
    };
  }),
  
  // Type-safe event handling
  handleExecutionEvent: (event) => set((state: UnifiedStore) => {
    switch (event.type) {
      case EventType.EXECUTION_STATUS_CHANGED:
        // Handle execution-level status changes
        if (event.data?.status === Status.RUNNING) {
          state.startExecution(event.execution_id);
        } else if (event.data?.status === Status.COMPLETED || 
                   event.data?.status === Status.FAILED) {
          state.stopExecution();
        } else if (event.data?.status === Status.PAUSED) {
          state.pauseExecution();
        }
        break;
        
      case EventType.NODE_STATUS_CHANGED:
        // Handle node-level status changes
        if (event.node_id && event.status) {
          const nodeState: StoreNodeState = {
            status: event.status,
            timestamp: event.timestamp ? new Date(event.timestamp).getTime() : Date.now(),
            error: event.error
          };
          updateNodeState(state, event.node_id as NodeID, nodeState);
        }
        break;
        
      case EventType.NODE_PROGRESS:
        // Handle node progress updates (e.g., streaming responses)
        if (event.node_id && event.data) {
          state.updateExecutionContext({ 
            [`${event.node_id}_progress`]: event.data 
          });
        }
        break;
        
      case EventType.EXECUTION_ERROR:
        // Handle execution errors
        if (event.error) {
          console.error('[ExecutionSlice] Execution error:', event.error);
          if (event.node_id) {
            state.setNodeFailed(event.node_id as NodeID, event.error);
          }
        }
        break;
        
      case EventType.EXECUTION_UPDATE:
        // Handle generic execution updates
        if (event.result && event.node_id) {
          state.updateExecutionContext({ 
            [event.node_id]: event.result 
          });
        }
        break;
        
      case EventType.INTERACTIVE_PROMPT:
      case EventType.INTERACTIVE_RESPONSE:
        // These are handled by other parts of the system
        break;
        
      default:
        console.warn('[ExecutionSlice] Unknown event type:', event.type);
    }
  })
});