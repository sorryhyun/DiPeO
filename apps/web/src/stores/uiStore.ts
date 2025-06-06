import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface UIStore {
  // Selection
  selection: { id: string; type: 'node' | 'arrow' | 'person' } | null;
  
  // Views
  activeView: 'diagram' | 'memory' | 'execution';
  activeCanvas: 'main' | 'memory';
  dashboardTab: 'properties' | 'persons' | 'conversation';
  
  // Modals
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  
  // Selection actions
  select: (id: string, type: 'node' | 'arrow' | 'person') => void;
  clearSelection: () => void;
  
  // View actions
  setActiveView: (view: 'diagram' | 'memory' | 'execution') => void;
  setActiveCanvas: (canvas: 'main' | 'memory') => void;
  toggleCanvas: () => void;
  setDashboardTab: (tab: 'properties' | 'persons' | 'conversation') => void;
  
  // Modal actions
  openApiKeysModal: () => void;
  closeApiKeysModal: () => void;
  openExecutionModal: () => void;
  closeExecutionModal: () => void;
  
  // Getters
  hasSelection: () => boolean;
  getSelectedId: () => string | null;
  getSelectedType: () => 'node' | 'arrow' | 'person' | null;
  
  // Legacy getters for compatibility
  selectedNodeId: string | null;
  selectedArrowId: string | null;
  selectedPersonId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedArrowId: (id: string | null) => void;
  setSelectedPersonId: (id: string | null) => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      selection: null,
      activeView: 'diagram',
      activeCanvas: 'main',
      dashboardTab: 'properties',
      showApiKeysModal: false,
      showExecutionModal: false,
      
      // Selection actions
      select: (id, type) => {
        set({ selection: { id, type } });
        // Auto-switch tab based on selection
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
      toggleCanvas: () => set({ activeCanvas: get().activeCanvas === 'main' ? 'memory' : 'main' }),
      setDashboardTab: (tab) => set({ dashboardTab: tab }),
      
      // Modal actions
      openApiKeysModal: () => set({ showApiKeysModal: true }),
      closeApiKeysModal: () => set({ showApiKeysModal: false }),
      openExecutionModal: () => set({ showExecutionModal: true }),
      closeExecutionModal: () => set({ showExecutionModal: false }),
      
      // Getters
      hasSelection: () => Boolean(get().selection),
      getSelectedId: () => get().selection?.id || null,
      getSelectedType: () => get().selection?.type || null,
      
      // Legacy getters for compatibility
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
      
      // Legacy setters for compatibility
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
    { name: 'ui-store' }
  )
);

// Export legacy alias
export const useConsolidatedUIStore = useUIStore;