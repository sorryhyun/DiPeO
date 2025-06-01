// Consolidated UI store - manages all UI-related state including selections and dashboard
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ConsolidatedUIState {
  // Selection state
  selectedNodeId: string | null;
  selectedArrowId: string | null;
  selectedPersonId: string | null;
  isMemoryLayerTilted: boolean;
  // Dashboard state (moved from diagram store)
  dashboardTab: 'persons' | 'conversation' | 'properties';

  // Selection actions
  setSelectedNodeId: (nodeId: string | null) => void;
  setSelectedArrowId: (arrowId: string | null) => void;
  setSelectedPersonId: (personId: string | null) => void;
  clearSelection: () => void;
  selectNode: (nodeId: string) => void;
  selectArrow: (arrowId: string) => void;
  selectPerson: (personId: string) => void;

  // Dashboard actions
  setDashboardTab: (tab: 'persons' | 'conversation' | 'properties') => void;

  setMemoryLayerTilted: (tilted: boolean) => void;
  toggleMemoryLayer: () => void;
  // Computed state
  hasSelection: () => boolean;
}

export const useConsolidatedUIStore = create<ConsolidatedUIState>()(
  devtools(
    (set, get) => ({
      // Initial state
      selectedNodeId: null,
      selectedArrowId: null,
      selectedPersonId: null,
      dashboardTab: 'properties',
      isMemoryLayerTilted: false,

      // Selection actions - each selection clears others
      setSelectedNodeId: (nodeId) => set({ 
        selectedNodeId: nodeId, 
        selectedArrowId: null,
        selectedPersonId: null 
      }),

      setSelectedArrowId: (arrowId) => set({
        selectedArrowId: arrowId,
        selectedNodeId: null,
        selectedPersonId: null 
      }),

      setSelectedPersonId: (personId) => set({ 
        selectedPersonId: personId, 
        selectedNodeId: null, 
        selectedArrowId: null
      }),

      clearSelection: () => set({ 
        selectedNodeId: null, 
        selectedArrowId: null,
        selectedPersonId: null 
      }),

      // Convenience selection methods
      selectNode: (nodeId: string) => {
        get().setSelectedNodeId(nodeId);
      },

      selectArrow: (arrowId: string) => {
        get().setSelectedArrowId(arrowId);
      },

      selectPerson: (personId: string) => {
        get().setSelectedPersonId(personId);
      },

      // Dashboard actions
      setDashboardTab: (tab) => set({ dashboardTab: tab }),

      setMemoryLayerTilted: (tilted) => set({ isMemoryLayerTilted: tilted }),
      toggleMemoryLayer: () => set((state) => ({ isMemoryLayerTilted: !state.isMemoryLayerTilted })),
      // Computed state
      hasSelection: () => {
        const state = get();
        return Boolean(state.selectedNodeId || state.selectedArrowId || state.selectedPersonId);
      },
    }),
    {
      name: 'consolidated-ui-store',
    }
  )
);