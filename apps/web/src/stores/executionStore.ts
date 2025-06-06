import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ExecutionStore {
  // Status
  isExecuting: boolean;
  executionId: string | null;
  
  // Node tracking
  currentRunningNode: string | null;
  runningNodes: string[];
  nodeRunningStates: Record<string, boolean>;
  skippedNodes: Record<string, { reason: string }>;
  nodeErrors: Record<string, string>;
  
  // Context
  runContext: Record<string, any>;
  lastUpdate: number;
  
  // Actions
  startExecution: (executionId: string) => void;
  stopExecution: () => void;
  reset: () => void;
  
  // Node management
  addRunningNode: (nodeId: string) => void;
  removeRunningNode: (nodeId: string) => void;
  setCurrentRunningNode: (nodeId: string | null) => void;
  addSkippedNode: (nodeId: string, reason: string) => void;
  setNodeError: (nodeId: string, error: string | null) => void;
  
  // Context
  setRunContext: (context: Record<string, any>) => void;
  
  // Getters
  isNodeRunning: (nodeId: string) => boolean;
  hasNodeError: (nodeId: string) => boolean;
  getNodeError: (nodeId: string) => string | null;
}

export const useExecutionStore = create<ExecutionStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      isExecuting: false,
      executionId: null,
      currentRunningNode: null,
      runningNodes: [],
      nodeRunningStates: {},
      skippedNodes: {},
      nodeErrors: {},
      runContext: {},
      lastUpdate: Date.now(),
      
      // Execution control
      startExecution: (executionId: string) => set({
        isExecuting: true,
        executionId,
        runningNodes: [],
        nodeRunningStates: {},
        skippedNodes: {},
        nodeErrors: {},
        runContext: {},
        lastUpdate: Date.now()
      }),
      
      stopExecution: () => set({
        isExecuting: false,
        executionId: null,
        currentRunningNode: null,
        runningNodes: [],
        nodeRunningStates: {},
        lastUpdate: Date.now()
      }),
      
      reset: () => set({
        isExecuting: false,
        executionId: null,
        currentRunningNode: null,
        runningNodes: [],
        nodeRunningStates: {},
        skippedNodes: {},
        nodeErrors: {},
        runContext: {},
        lastUpdate: Date.now()
      }),
      addRunningNode: (nodeId: string) => set((state) => ({
        runningNodes: [...state.runningNodes, nodeId],
        nodeRunningStates: { ...state.nodeRunningStates, [nodeId]: true },
        lastUpdate: Date.now()
      })),
      removeRunningNode: (nodeId: string) => set((state) => ({
        runningNodes: state.runningNodes.filter(id => id !== nodeId),
        nodeRunningStates: { ...state.nodeRunningStates, [nodeId]: false },
        lastUpdate: Date.now()
      })),
      setCurrentRunningNode: (nodeId: string | null) => set({
        currentRunningNode: nodeId,
        lastUpdate: Date.now()
      }),
      
      addSkippedNode: (nodeId: string, reason: string) => set((state) => ({
        skippedNodes: { ...state.skippedNodes, [nodeId]: { reason } },
        lastUpdate: Date.now()
      })),
      
      setNodeError: (nodeId: string, error: string | null) => set((state) => {
        const nodeErrors = { ...state.nodeErrors };
        if (error) {
          nodeErrors[nodeId] = error;
        } else {
          delete nodeErrors[nodeId];
        }
        return { nodeErrors, lastUpdate: Date.now() };
      }),
      
      setRunContext: (context: Record<string, any>) => set({
        runContext: context,
        lastUpdate: Date.now()
      }),
      
      // Getters
      isNodeRunning: (nodeId: string) => get().runningNodes.includes(nodeId),
      
      hasNodeError: (nodeId: string) => Boolean(get().nodeErrors[nodeId]),
      
      getNodeError: (nodeId: string) => get().nodeErrors[nodeId] || null
    }),
    { name: 'execution-store' }
  )
);