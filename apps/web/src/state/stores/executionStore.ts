import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ExecutionState {
  isExecuting: boolean;
  currentRunningNode: string | null;
  runningNodes: string[];
  nodeRunningStates: Record<string, boolean>;
  skippedNodes: Record<string, { reason: string }>;
  lastUpdate: number;
  runContext?: any;
  reset: () => void;
  addRunningNode: (nodeId: string) => void;
  removeRunningNode: (nodeId: string) => void;
  setCurrentRunningNode: (nodeId: string | null) => void;
  setRunContext: (context: any) => void;
  addSkippedNode: (nodeId: string, reason: string) => void;
}

export const useExecutionStore = create<ExecutionState>()(
  devtools(
    (set, get) => ({
      isExecuting: false,
      currentRunningNode: null,
      runningNodes: [],
      nodeRunningStates: {},
      skippedNodes: {},
      lastUpdate: Date.now(),
      runContext: undefined,
      reset: () => set({
        isExecuting: false,
        currentRunningNode: null,
        runningNodes: [],
        nodeRunningStates: {},
        skippedNodes: {},
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
      setRunContext: (context: any) => set({
        runContext: context,
        lastUpdate: Date.now()
      }),
      addSkippedNode: (nodeId: string, reason: string) => set((state) => ({
        skippedNodes: { ...state.skippedNodes, [nodeId]: { reason } },
        lastUpdate: Date.now()
      }))
    }),
    { name: 'execution-store' }
  )
);