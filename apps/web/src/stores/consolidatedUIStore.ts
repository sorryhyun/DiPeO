import { createWithEqualityFn } from 'zustand/traditional';
import { devtools } from 'zustand/middleware';
import { NodeID, ArrowID, PersonID, nodeId, arrowId, personId } from '@/types/branded';

export type SelectionType = 'node' | 'arrow' | 'person';

export interface Selection {
  id: NodeID | ArrowID | PersonID;
  type: SelectionType;
}

export interface ConsolidatedUIState {
  // Selection state (unified from all stores)
  selection: Selection | null;
  
  // View state
  activeView: 'diagram' | 'execution';
  activeCanvas: 'main' | 'execution';
  dashboardTab: 'properties' | 'persons' | 'conversation';
  
  // Modal state
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  
  // Selection actions (unified interface) - using branded types
  selectNode: (id: NodeID) => void;
  selectArrow: (id: ArrowID) => void;
  selectPerson: (id: PersonID) => void;
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
  getSelectedId: () => NodeID | ArrowID | PersonID | null;
  getSelectedType: () => SelectionType | null;
  isNodeSelected: (id: NodeID) => boolean;
  isArrowSelected: (id: ArrowID) => boolean;
  isPersonSelected: (id: PersonID) => boolean;
  
  // Legacy compatibility getters
  selectedNodeId: string | null;
  selectedArrowId: string | null;
  selectedPersonId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedArrowId: (id: string | null) => void;
  setSelectedPersonId: (id: string | null) => void;
}

export const useConsolidatedUIStore = createWithEqualityFn<ConsolidatedUIState>()(
  devtools(
    (set, get) => ({
      // Initial state
      selection: null,
      activeView: 'diagram',
      activeCanvas: 'main',
      dashboardTab: 'properties',
      showApiKeysModal: false,
      showExecutionModal: false,
      
      // Selection actions (unified interface) - using branded types
      selectNode: (id: NodeID) => {
        console.log('[consolidatedUIStore] selectNode:', id);
        set({ 
          selection: { id, type: 'node' },
          // Update legacy compatibility fields
          selectedNodeId: id as string,
          selectedArrowId: null,
          selectedPersonId: null,
          dashboardTab: 'properties'
        });
      },
      
      selectArrow: (id: ArrowID) => {
        console.log('[consolidatedUIStore] selectArrow:', id);
        set({ 
          selection: { id, type: 'arrow' },
          // Update legacy compatibility fields
          selectedNodeId: null,
          selectedArrowId: id as string,
          selectedPersonId: null,
          dashboardTab: 'properties'
        });
      },
      
      selectPerson: (id: PersonID) => {
        console.log('[consolidatedUIStore] selectPerson:', id);
        set({ 
          selection: { id, type: 'person' },
          // Update legacy compatibility fields
          selectedNodeId: null,
          selectedArrowId: null,
          selectedPersonId: id as string,
          dashboardTab: 'persons'
        });
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
      isNodeSelected: (id: NodeID) => {
        const selection = get().selection;
        return selection?.type === 'node' && selection.id === id;
      },
      isArrowSelected: (id: ArrowID) => {
        const selection = get().selection;
        return selection?.type === 'arrow' && selection.id === id;
      },
      isPersonSelected: (id: PersonID) => {
        const selection = get().selection;
        return selection?.type === 'person' && selection.id === id;
      },
      
      // Legacy compatibility - computed as state fields
      selectedNodeId: null,
      selectedArrowId: null,
      selectedPersonId: null,
      
      // Legacy compatibility setters
      setSelectedNodeId: (id) => {
        console.log('[consolidatedUIStore] setSelectedNodeId:', id);
        if (id) {
          const brandedId = nodeId(id);
          set({ 
            selection: { id: brandedId, type: 'node' },
            selectedNodeId: id,
            selectedArrowId: null,
            selectedPersonId: null,
            dashboardTab: 'properties'
          });
        } else {
          set({ 
            selection: null,
            selectedNodeId: null,
            selectedArrowId: null,
            selectedPersonId: null,
          });
        }
      },
      setSelectedArrowId: (id) => {
        console.log('[consolidatedUIStore] setSelectedArrowId:', id);
        if (id) {
          const brandedId = arrowId(id);
          set({ 
            selection: { id: brandedId, type: 'arrow' },
            selectedNodeId: null,
            selectedArrowId: id,
            selectedPersonId: null,
            dashboardTab: 'properties'
          });
        } else {
          set({ 
            selection: null,
            selectedNodeId: null,
            selectedArrowId: null,
            selectedPersonId: null,
          });
        }
      },
      setSelectedPersonId: (id) => {
        console.log('[consolidatedUIStore] setSelectedPersonId:', id);
        if (id) {
          const brandedId = personId(id);
          set({ 
            selection: { id: brandedId, type: 'person' },
            selectedNodeId: null,
            selectedArrowId: null,
            selectedPersonId: id,
            dashboardTab: 'persons'
          });
        } else {
          set({ 
            selection: null,
            selectedNodeId: null,
            selectedArrowId: null,
            selectedPersonId: null,
          });
        }
      }
    }),
    { name: 'consolidated-ui-store' }
  )
);