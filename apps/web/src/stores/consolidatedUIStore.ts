import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ConsolidatedUIState {
  // Selection state (unified from all stores)
  selection: { id: string; type: 'node' | 'arrow' | 'person' } | null;
  
  // View state
  activeView: 'diagram' | 'execution';
  activeCanvas: 'main' | 'execution';
  dashboardTab: 'properties' | 'persons' | 'conversation';
  
  // Modal state
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  
  // Selection actions (unified interface)
  select: (id: string, type: 'node' | 'arrow' | 'person') => void;
  clearSelection: () => void;
  
  // View actions
  setActiveView: (view: 'diagram' | 'execution' ) => void;
  setActiveCanvas: (canvas: 'main' | 'execution') => void;
  setDashboardTab: (tab: 'properties' | 'persons' | 'conversation') => void;
  toggleCanvas: () => void;
  
  // Modal actions
  openApiKeysModal: () => void;
  closeApiKeysModal: () => void;
  openExecutionModal: () => void;
  closeExecutionModal: () => void;
  
  // Computed getters
  hasSelection: () => boolean;
  getSelectedId: () => string | null;
  getSelectedType: () => 'node' | 'arrow' | 'person' | null;
  
  // Legacy compatibility getters
  selectedNodeId: string | null;
  selectedArrowId: string | null;
  selectedPersonId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedArrowId: (id: string | null) => void;
  setSelectedPersonId: (id: string | null) => void;
}

export const useConsolidatedUIStore = create<ConsolidatedUIState>()(
  devtools(
    (set, get) => ({
      // Initial state
      selection: null,
      activeView: 'diagram',
      activeCanvas: 'main',
      dashboardTab: 'properties',
      showApiKeysModal: false,
      showExecutionModal: false,
      
      // Selection actions (unified interface)
      select: (id, type) => {
        console.log('[consolidatedUIStore] select:', { id, type });
        set({ 
          selection: { id, type },
          // Update legacy compatibility fields
          selectedNodeId: type === 'node' ? id : null,
          selectedArrowId: type === 'arrow' ? id : null,
          selectedPersonId: type === 'person' ? id : null,
        });
        // Auto-switch dashboard tab based on selection
        if (type === 'person') {
          set({ dashboardTab: 'persons' });
        } else {
          set({ dashboardTab: 'properties' });
        }
      },
      
      clearSelection: () => set({ 
        selection: null,
        selectedNodeId: null,
        selectedArrowId: null,
        selectedPersonId: null,
      }),
      
      // View actions
      setActiveView: (view) => set({ activeView: view }),
      setActiveCanvas: (canvas) => set({ activeCanvas: canvas }),
      setDashboardTab: (tab) => set({ dashboardTab: tab }),
      toggleCanvas: () => set({ activeCanvas: get().activeCanvas === 'main' ? 'execution' : 'main' }),
      
      // Modal actions
      openApiKeysModal: () => set({ showApiKeysModal: true }),
      closeApiKeysModal: () => set({ showApiKeysModal: false }),
      openExecutionModal: () => set({ showExecutionModal: true }),
      closeExecutionModal: () => set({ showExecutionModal: false }),
      
      // Computed getters
      hasSelection: () => Boolean(get().selection),
      getSelectedId: () => get().selection?.id || null,
      getSelectedType: () => get().selection?.type || null,
      
      // Legacy compatibility - computed as state fields
      selectedNodeId: null,
      selectedArrowId: null,
      selectedPersonId: null,
      
      // Legacy compatibility setters
      setSelectedNodeId: (id) => {
        console.log('[consolidatedUIStore] setSelectedNodeId:', id);
        set({ 
          selection: id ? { id, type: 'node' } : null,
          selectedNodeId: id,
          selectedArrowId: null,
          selectedPersonId: null,
          dashboardTab: id ? 'properties' : get().dashboardTab
        });
      },
      setSelectedArrowId: (id) => {
        set({ 
          selection: id ? { id, type: 'arrow' } : null,
          selectedNodeId: null,
          selectedArrowId: id,
          selectedPersonId: null,
          dashboardTab: id ? 'properties' : get().dashboardTab
        });
      },
      setSelectedPersonId: (id) => {
        set({ 
          selection: id ? { id, type: 'person' } : null,
          selectedNodeId: null,
          selectedArrowId: null,
          selectedPersonId: id,
          dashboardTab: id ? 'persons' : get().dashboardTab
        });
      }
    }),
    { name: 'consolidated-ui-store' }
  )
);