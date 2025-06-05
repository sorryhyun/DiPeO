import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface AppStore {
  // UI State
  selection: { id: string; type: 'node' | 'arrow' | 'person' } | null;
  activeView: 'diagram' | 'memory' | 'execution';
  dashboardTab: 'persons' | 'conversation' | 'properties';
  
  // Execution State
  execution: {
    isRunning: boolean;
    executionId: string | null;
    runningNodes: string[];
    context: Record<string, any>;
    errors: Record<string, string>;
  };
  
  // UI Actions
  select: (id: string, type: 'node' | 'arrow' | 'person') => void;
  clearSelection: () => void;
  setView: (view: 'diagram' | 'memory' | 'execution') => void;
  setDashboardTab: (tab: 'persons' | 'conversation' | 'properties') => void;
  
  // Execution Actions
  startExecution: (executionId: string) => void;
  stopExecution: () => void;
  setNodeRunning: (nodeId: string, isRunning: boolean) => void;
  setExecutionContext: (context: Record<string, any>) => void;
  setNodeError: (nodeId: string, error: string | null) => void;
  
  // Computed
  isNodeRunning: (nodeId: string) => boolean;
  getSelectedId: () => string | null;
  getSelectedType: () => 'node' | 'arrow' | 'person' | null;
}

export const useAppStore = create<AppStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      selection: null,
      activeView: 'diagram',
      dashboardTab: 'properties',
      execution: {
        isRunning: false,
        executionId: null,
        runningNodes: [],
        context: {},
        errors: {}
      },
      
      // UI Actions
      select: (id, type) => {
        set({ selection: { id, type } });
        // Auto-switch to properties tab when selecting
        if (type === 'person') {
          set({ dashboardTab: 'persons' });
        } else {
          set({ dashboardTab: 'properties' });
        }
      },
      
      clearSelection: () => set({ selection: null }),
      
      setView: (view) => set({ activeView: view }),
      
      setDashboardTab: (tab) => set({ dashboardTab: tab }),
      
      // Execution Actions
      startExecution: (executionId) => {
        set({
          execution: {
            isRunning: true,
            executionId,
            runningNodes: [],
            context: {},
            errors: {}
          }
        });
      },
      
      stopExecution: () => {
        set((state) => ({
          execution: {
            ...state.execution,
            isRunning: false,
            executionId: null,
            runningNodes: []
          }
        }));
      },
      
      setNodeRunning: (nodeId, isRunning) => {
        set((state) => ({
          execution: {
            ...state.execution,
            runningNodes: isRunning
              ? [...state.execution.runningNodes, nodeId]
              : state.execution.runningNodes.filter(id => id !== nodeId)
          }
        }));
      },
      
      setExecutionContext: (context) => {
        set((state) => ({
          execution: {
            ...state.execution,
            context
          }
        }));
      },
      
      setNodeError: (nodeId, error) => {
        set((state) => {
          const errors = { ...state.execution.errors };
          if (error) {
            errors[nodeId] = error;
          } else {
            delete errors[nodeId];
          }
          return {
            execution: {
              ...state.execution,
              errors
            }
          };
        });
      },
      
      // Computed
      isNodeRunning: (nodeId) => {
        return get().execution.runningNodes.includes(nodeId);
      },
      
      getSelectedId: () => get().selection?.id || null,
      
      getSelectedType: () => get().selection?.type || null
    }),
    {
      name: 'app-store'
    }
  )
);