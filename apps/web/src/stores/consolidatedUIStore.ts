import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface ConsolidatedUIState {
  // Selection state (unified from all stores)
  selection: { id: string; type: 'node' | 'arrow' | 'person' } | null;
  
  // View state
  activeView: 'diagram' | 'memory' | 'execution';
  activeCanvas: 'main' | 'memory';
  dashboardTab: 'properties' | 'persons' | 'conversation';
  
  // Modal state
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  
  // Selection actions (unified interface)
  select: (id: string, type: 'node' | 'arrow' | 'person') => void;
  clearSelection: () => void;
  
  // View actions
  setActiveView: (view: 'diagram' | 'memory' | 'execution') => void;
  setActiveCanvas: (canvas: 'main' | 'memory') => void;
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
        set({ selection: { id, type } });
        // Auto-switch dashboard tab based on selection
        if (type === 'person') {
          set({ dashboardTab: 'persons' });
        } else {
          set({ dashboardTab: 'properties' });
        }
      },
      
      clearSelection: () => set({ selection: null }),
      
      // View actions
      setActiveView: (view) => set({ activeView: view }),
      setActiveCanvas: (canvas) => set({ activeCanvas: canvas }),
      setDashboardTab: (tab) => set({ dashboardTab: tab }),
      toggleCanvas: () => set({ activeCanvas: get().activeCanvas === 'main' ? 'memory' : 'main' }),
      
      // Modal actions
      openApiKeysModal: () => set({ showApiKeysModal: true }),
      closeApiKeysModal: () => set({ showApiKeysModal: false }),
      openExecutionModal: () => set({ showExecutionModal: true }),
      closeExecutionModal: () => set({ showExecutionModal: false }),
      
      // Computed getters
      hasSelection: () => Boolean(get().selection),
      getSelectedId: () => get().selection?.id || null,
      getSelectedType: () => get().selection?.type || null,
      
      // Legacy compatibility getters
      get selectedNodeId() {
        const selection = get().selection;
        return selection?.type === 'node' ? selection.id : null;
      },
      get selectedArrowId() {
        const selection = get().selection;
        return selection?.type === 'arrow' ? selection.id : null;
      },
      get selectedPersonId() {
        const selection = get().selection;
        return selection?.type === 'person' ? selection.id : null;
      },
      
      // Legacy compatibility setters
      setSelectedNodeId: (id) => {
        if (id) {
          get().select(id, 'node');
        } else {
          get().clearSelection();
        }
      },
      setSelectedArrowId: (id) => {
        if (id) {
          get().select(id, 'arrow');
        } else {
          get().clearSelection();
        }
      },
      setSelectedPersonId: (id) => {
        if (id) {
          get().select(id, 'person');
        } else {
          get().clearSelection();
        }
      }
    }),
    { name: 'consolidated-ui-store' }
  )
);