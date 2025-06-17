import { StateCreator } from 'zustand';
import { immer } from 'zustand/middleware/immer';

export interface DiagramSlice {
  // TODO: Move diagram-related state from unified store
  nodes: any[];
  edges: any[];
  selectedNodeId: string | null;
  
  // Actions
  setNodes: (nodes: any[]) => void;
  setEdges: (edges: any[]) => void;
  selectNode: (nodeId: string | null) => void;
}

export const createDiagramSlice: StateCreator<
  DiagramSlice,
  [['zustand/immer', never]],
  [],
  DiagramSlice
> = (set) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  
  setNodes: (nodes) => set((state) => { 
    state.nodes = nodes; 
  }),
  setEdges: (edges) => set((state) => { 
    state.edges = edges; 
  }),
  selectNode: (nodeId) => set((state) => { 
    state.selectedNodeId = nodeId; 
  }),
});
