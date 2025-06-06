import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ConsolidatedUIState {
  selectedNodeId: string | null;
  selectedArrowId: string | null;
  selectedPersonId: string | null;
  dashboardTab: string;
  activeCanvas: string;
  
  setSelectedNodeId: (id: string | null) => void;
  setSelectedArrowId: (id: string | null) => void;
  setSelectedPersonId: (id: string | null) => void;
  clearSelection: () => void;
  setDashboardTab: (tab: string) => void;
  setActiveCanvas: (canvas: string) => void;
  toggleCanvas: () => void;
  hasSelection: () => boolean;
}

export const useConsolidatedUIStore = create<ConsolidatedUIState>()(
  devtools(
    (set, get) => ({
      selectedNodeId: null,
      selectedArrowId: null,
      selectedPersonId: null,
      dashboardTab: 'properties',
      activeCanvas: 'main',
      
      setSelectedNodeId: (id) => set({ selectedNodeId: id }),
      setSelectedArrowId: (id) => set({ selectedArrowId: id }),
      setSelectedPersonId: (id) => set({ selectedPersonId: id }),
      clearSelection: () => set({ selectedNodeId: null, selectedArrowId: null, selectedPersonId: null }),
      setDashboardTab: (tab) => set({ dashboardTab: tab }),
      setActiveCanvas: (canvas) => set({ activeCanvas: canvas }),
      toggleCanvas: () => set({ activeCanvas: get().activeCanvas === 'main' ? 'memory' : 'main' }),
      hasSelection: () => Boolean(get().selectedNodeId || get().selectedArrowId || get().selectedPersonId)
    }),
    { name: 'consolidated-ui-store' }
  )
);