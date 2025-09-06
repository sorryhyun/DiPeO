import { createStore } from 'zustand/vanilla';

export type NodeEvent = {
  nodeId: string;
  status: string;
  timestamp: number;
  error?: string | null;
  outputs?: any;
};

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
  nodeEvents: NodeEvent[]; // Track all node events chronologically
  startedAt: number | null;
  finishedAt: number | null;
  diagramName?: string;
  edges?: Array<{ id?: string; source: string; target: string; data?: any }>;
  nodes?: Array<{ id: string; type: string; position?: { x: number; y: number }; data: any }>;
  handles?: Array<{ id: string; node_id: string; label: string; direction: string; data_type: string; position?: string }>;
};

export type ExecutionLocalStoreActions = {
  setExecutionId: (id: string) => void;
  setRunning: (isRunning: boolean) => void;
  updateNodeState: (nodeId: string, state: { status: string; timestamp: number; error?: string | null; outputs?: any }) => void;
  addNodeEvent: (event: NodeEvent) => void;
  addRunningNode: (nodeId: string) => void;
  removeRunningNode: (nodeId: string) => void;
  setStartedAt: (timestamp: number) => void;
  setFinishedAt: (timestamp: number) => void;
  setDiagramData: (name: string, nodes: any[], edges: any[], handles?: any[]) => void;
  reset: () => void;
};

export type ExecutionLocalStore = StoreExecutionState & ExecutionLocalStoreActions;

export const createExecutionLocalStore = () =>
  createStore<ExecutionLocalStore>((set, get) => ({
    id: null,
    isRunning: false,
    runningNodes: new Set(),
    nodeStates: new Map(),
    nodeEvents: [],
    startedAt: null,
    finishedAt: null,
    diagramName: undefined,
    edges: undefined,
    nodes: undefined,
    handles: undefined,

    setExecutionId: (id: string) => set({ id }),

    setRunning: (isRunning: boolean) => set({ isRunning }),

    updateNodeState: (nodeId: string, state) =>
      set((prev) => {
        const newNodeStates = new Map(prev.nodeStates);
        newNodeStates.set(nodeId, state);
        // Also add to events array
        const newEvent: NodeEvent = {
          nodeId,
          status: state.status,
          timestamp: state.timestamp,
          error: state.error,
          outputs: state.outputs,
        };
        return {
          nodeStates: newNodeStates,
          nodeEvents: [...prev.nodeEvents, newEvent]
        };
      }),

    addNodeEvent: (event: NodeEvent) =>
      set((prev) => ({
        nodeEvents: [...prev.nodeEvents, event]
      })),

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

    setDiagramData: (name: string, nodes: any[], edges: any[], handles?: any[]) =>
      set({ diagramName: name, nodes, edges, handles }),

    reset: () => set({
      id: null,
      isRunning: false,
      runningNodes: new Set(),
      nodeStates: new Map(),
      nodeEvents: [],
      startedAt: null,
      finishedAt: null,
      diagramName: undefined,
      edges: undefined,
      nodes: undefined,
      handles: undefined,
    }),
  }));
