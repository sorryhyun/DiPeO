// Execution state store for diagram running and streaming
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ExecutionState {
  // Execution state
  isExecuting: boolean;
  executionId: string | null;
  runContext: Record<string, unknown>;
  runningNodes: string[];
  currentRunningNode: string | null;
  nodeRunningStates: Record<string, boolean>;
  skippedNodes: Record<string, { reason: string; timestamp: number }>;
  lastUpdate?: number;
  
  // Stream connection
  streamConnection: EventSource | null;
  
  // Actions
  startExecution: (executionId: string) => void;
  completeExecution: () => void;
  updateNodeStatus: (nodeId: string, status: 'running' | 'complete' | 'error' | 'skipped', reason?: string) => void;
  setRunContext: (context: Record<string, unknown>) => void;
  clearRunContext: () => void;
  setRunningNodes: (nodeIds: string[]) => void;
  addRunningNode: (nodeId: string) => void;
  removeRunningNode: (nodeId: string) => void;
  clearRunningNodes: () => void;
  setCurrentRunningNode: (nodeId: string | null) => void;
  addSkippedNode: (nodeId: string, reason: string) => void;
  
  // Stream management
  connectStream: (url: string) => void;
  disconnectStream: () => void;
}

export const useExecutionStore = create<ExecutionState>()(
  devtools(
    (set, get) => ({
      // State
      isExecuting: false,
      executionId: null,
      runContext: {},
      runningNodes: [],
      currentRunningNode: null,
      nodeRunningStates: {},
      skippedNodes: {},
      streamConnection: null,

      // Execution control
      startExecution: (executionId) => set({ 
        isExecuting: true, 
        executionId,
        runningNodes: [],
        nodeRunningStates: {},
        skippedNodes: {},
        currentRunningNode: null
      }),
      
      completeExecution: () => set({ 
        isExecuting: false, 
        executionId: null,
        currentRunningNode: null
      }),
      
      updateNodeStatus: (nodeId, status, reason) => {
        if (status === 'running') {
          get().addRunningNode(nodeId);
          set({ currentRunningNode: nodeId });
        } else if (status === 'complete' || status === 'error') {
          get().removeRunningNode(nodeId);
          if (get().currentRunningNode === nodeId) {
            set({ currentRunningNode: null });
          }
        } else if (status === 'skipped' && reason) {
          get().removeRunningNode(nodeId);
          get().addSkippedNode(nodeId, reason);
          if (get().currentRunningNode === nodeId) {
            set({ currentRunningNode: null });
          }
        }
      },

      // Context management
      setRunContext: (context) => set({ runContext: context }),
      clearRunContext: () => set({ runContext: {} }),

      // Node tracking
      setRunningNodes: (nodeIds) => set({ runningNodes: nodeIds }),
      addRunningNode: (nodeId) => {
        console.log('[ExecutionStore] addRunningNode called with:', nodeId);
        set((state) => {
          const newRunningNodes = state.runningNodes.includes(nodeId) 
            ? state.runningNodes 
            : [...state.runningNodes, nodeId];
          const newNodeRunningStates = {
            ...state.nodeRunningStates,
            [nodeId]: true
          };
          console.log('[ExecutionStore] Updated running nodes:', newRunningNodes);
          console.log('[ExecutionStore] Updated node running states:', newNodeRunningStates);
          return {
            runningNodes: newRunningNodes,
            nodeRunningStates: newNodeRunningStates,
            lastUpdate: Date.now()
          };
        });
      },
      
      removeRunningNode: (nodeId) => {
        console.log('[ExecutionStore] removeRunningNode called with:', nodeId);
        set((state) => {
          const newRunningNodes = state.runningNodes.filter(id => id !== nodeId);
          const newNodeRunningStates = Object.fromEntries(
            Object.entries(state.nodeRunningStates).filter(([id]) => id !== nodeId)
          );
          console.log('[ExecutionStore] Updated running nodes:', newRunningNodes);
          console.log('[ExecutionStore] Updated node running states:', newNodeRunningStates);
          return {
            runningNodes: newRunningNodes,
            nodeRunningStates: newNodeRunningStates,
            lastUpdate: Date.now()
          };
        });
      },
      clearRunningNodes: () => set({ runningNodes: [], nodeRunningStates: {} }),
      setCurrentRunningNode: (nodeId) => set({ currentRunningNode: nodeId }),
      
      addSkippedNode: (nodeId, reason) => {
        set((state) => ({
          skippedNodes: {
            ...state.skippedNodes,
            [nodeId]: { reason, timestamp: Date.now() }
          }
        }));
      },
      
      // Stream management
      connectStream: (url) => {
        const currentConnection = get().streamConnection;
        if (currentConnection) {
          currentConnection.close();
        }
        
        const eventSource = new EventSource(url);
        set({ streamConnection: eventSource });
      },
      
      disconnectStream: () => {
        const connection = get().streamConnection;
        if (connection) {
          connection.close();
          set({ streamConnection: null });
        }
      },
    }),
    {
      name: 'execution-store',
    }
  )
);