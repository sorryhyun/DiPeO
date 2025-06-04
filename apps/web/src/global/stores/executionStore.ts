// Execution state store for diagram running and streaming
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ExecutionState {
  runContext: Record<string, unknown>;
  runningNodes: string[];
  currentRunningNode: string | null;
  nodeRunningStates: Record<string, boolean>; // Add this to track running states
  lastUpdate?: number; // Force re-renders with timestamp

  // Actions
  setRunContext: (context: Record<string, unknown>) => void;
  clearRunContext: () => void;
  setRunningNodes: (nodeIds: string[]) => void;
  addRunningNode: (nodeId: string) => void;
  removeRunningNode: (nodeId: string) => void;
  clearRunningNodes: () => void;
  setCurrentRunningNode: (nodeId: string | null) => void;
}

export const useExecutionStore = create<ExecutionState>()(
  devtools(
    (set) => ({
      runContext: {},
      runningNodes: [],
      currentRunningNode: null,
      nodeRunningStates: {}, // Add this to track running states

      setRunContext: (context) => set({ runContext: context }),
      clearRunContext: () => set({ runContext: {} }),

      setRunningNodes: (nodeIds) => set({ runningNodes: nodeIds }),
      addRunningNode: (nodeId) => {
        console.log('[ExecutionStore] Adding running node:', nodeId);
        set((state) => ({
          runningNodes: state.runningNodes.includes(nodeId) 
            ? state.runningNodes 
            : [...state.runningNodes, nodeId],
          nodeRunningStates: {
            ...state.nodeRunningStates,
            [nodeId]: true
          },
          lastUpdate: Date.now()
        }));
      },
      
      removeRunningNode: (nodeId) => {
        set((state) => ({
          runningNodes: state.runningNodes.filter(id => id !== nodeId),
          nodeRunningStates: Object.fromEntries(
            Object.entries(state.nodeRunningStates).filter(([id]) => id !== nodeId)
          ),
          lastUpdate: Date.now()
        }));
      },
      clearRunningNodes: () => set({ runningNodes: [], nodeRunningStates: {} }),
      setCurrentRunningNode: (nodeId) => set({ currentRunningNode: nodeId }),
    }),
    {
      name: 'execution-store',
    }
  )
);