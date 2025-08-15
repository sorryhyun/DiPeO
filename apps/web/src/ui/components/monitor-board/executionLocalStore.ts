import { createStore } from 'zustand/vanilla';

export type StoreExecutionState = {
  id: string | null;
  isRunning: boolean;
  runningNodes: Set<string>;
  nodeStates: Map<string, { 
    status: string; 
    timestamp: number; 
    error?: string | null;
    outputs?: any;
  }>;
  startedAt: number | null;
  finishedAt: number | null;
  diagramName?: string;
  edges?: Array<{ source: string; target: string }>;
  nodes?: Array<{ id: string; type: string; data: any }>;
};

export type ExecutionLocalStoreActions = {
  setExecutionId: (id: string) => void;
  setRunning: (isRunning: boolean) => void;
  updateNodeState: (nodeId: string, state: { status: string; timestamp: number; error?: string | null; outputs?: any }) => void;
  addRunningNode: (nodeId: string) => void;
  removeRunningNode: (nodeId: string) => void;
  setStartedAt: (timestamp: number) => void;
  setFinishedAt: (timestamp: number) => void;
  setDiagramData: (name: string, nodes: any[], edges: any[]) => void;
  reset: () => void;
};

export type ExecutionLocalStore = StoreExecutionState & ExecutionLocalStoreActions;

export const createExecutionLocalStore = () => 
  createStore<ExecutionLocalStore>((set, get) => ({
    id: null,
    isRunning: false,
    runningNodes: new Set(),
    nodeStates: new Map(),
    startedAt: null,
    finishedAt: null,
    diagramName: undefined,
    edges: undefined,
    nodes: undefined,

    setExecutionId: (id: string) => set({ id }),
    
    setRunning: (isRunning: boolean) => set({ isRunning }),
    
    updateNodeState: (nodeId: string, state) => 
      set((prev) => {
        const newNodeStates = new Map(prev.nodeStates);
        newNodeStates.set(nodeId, state);
        return { nodeStates: newNodeStates };
      }),
    
    addRunningNode: (nodeId: string) =>
      set((prev) => {
        const newRunningNodes = new Set(prev.runningNodes);
        newRunningNodes.add(nodeId);
        return { runningNodes: newRunningNodes };
      }),
    
    removeRunningNode: (nodeId: string) =>
      set((prev) => {
        const newRunningNodes = new Set(prev.runningNodes);
        newRunningNodes.delete(nodeId);
        return { runningNodes: newRunningNodes };
      }),
    
    setStartedAt: (timestamp: number) => set({ startedAt: timestamp }),
    
    setFinishedAt: (timestamp: number) => set({ finishedAt: timestamp }),
    
    setDiagramData: (name: string, nodes: any[], edges: any[]) => 
      set({ diagramName: name, nodes, edges }),
    
    reset: () => set({
      id: null,
      isRunning: false,
      runningNodes: new Set(),
      nodeStates: new Map(),
      startedAt: null,
      finishedAt: null,
      diagramName: undefined,
      edges: undefined,
      nodes: undefined,
    }),
  }));