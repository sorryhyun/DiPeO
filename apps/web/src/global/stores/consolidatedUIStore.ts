// Consolidated UI store - manages all UI-related state including selections and dashboard
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ConsolidatedUIState {
  // Selection state
  selectedNodeId: string | null;
  selectedArrowId: string | null;
  selectedPersonId: string | null;
  
  // Canvas state - new approach to replace memory layer tilting
  activeCanvas: 'diagram' | 'memory';
  
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

  // Canvas actions - new approach
  setActiveCanvas: (canvas: 'diagram' | 'memory') => void;
  toggleCanvas: () => void;
  
  // Backward compatibility - deprecated but kept for transition
  isMemoryLayerTilted: boolean;
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
      activeCanvas: 'diagram',
      
      // Backward compatibility
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

      // Canvas actions - new approach
      setActiveCanvas: (canvas) => set({ activeCanvas: canvas }),
      toggleCanvas: () => set((state) => ({ 
        activeCanvas: state.activeCanvas === 'diagram' ? 'memory' : 'diagram' 
      })),

      // Backward compatibility - deprecated
      setMemoryLayerTilted: (tilted) => set({ 
        isMemoryLayerTilted: tilted,
        activeCanvas: tilted ? 'memory' : 'diagram'
      }),
      toggleMemoryLayer: () => {
        const state = get();
        set({ 
          isMemoryLayerTilted: !state.isMemoryLayerTilted,
          activeCanvas: !state.isMemoryLayerTilted ? 'memory' : 'diagram'
        });
      },
      
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