import { StateCreator } from 'zustand';
import { ArrowID, NodeID, PersonID } from '@/core/types';
import { Vec2 } from '@dipeo/domain-models';
import { UnifiedStore } from '../unifiedStore.types';

export type SelectableID = NodeID | ArrowID | PersonID;
export type SelectableType = 'node' | 'arrow' | 'person';
export type ActiveView = 'diagram' | 'execution' | 'persons' | 'apikeys';
export type ActiveCanvas = 'main' | 'execution' | 'memory' | 'preview' | 'monitor';
export type DashboardTab = 'properties' | 'persons' | 'settings' | 'history';

export interface UISlice {
  // Selection state
  selectedId: SelectableID | null;
  selectedType: SelectableType | null;
  multiSelectedIds: Set<SelectableID>;
  
  // Highlight state (separate from selection)
  highlightedPersonId: PersonID | null;
  
  // View state
  activeView: ActiveView;
  activeCanvas: ActiveCanvas;
  dashboardTab: DashboardTab;
  
  // Viewport state
  zoom: number;
  position: Vec2;
  
  // Mode state
  readOnly: boolean;
  executionReadOnly: boolean;
  isDragging: boolean;
  isConnecting: boolean;
  
  // Modal state
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  showSettingsModal: boolean;
  showPersonModal: boolean;
  
  // Selection operations
  select: (id: SelectableID, type: SelectableType) => void;
  multiSelect: (ids: SelectableID[], type: SelectableType) => void;
  toggleSelection: (id: SelectableID, type: SelectableType) => void;
  clearSelection: () => void;
  selectAll: () => void;
  
  // Highlight operations
  highlightPerson: (personId: PersonID | null) => void;
  
  // View operations
  setActiveView: (view: ActiveView) => void;
  setActiveCanvas: (canvas: ActiveCanvas) => void;
  setDashboardTab: (tab: DashboardTab) => void;
  
  // Viewport operations
  setViewport: (zoom: number, position: Vec2) => void;
  setZoom: (zoom: number) => void;
  setPosition: (position: Vec2) => void;
  
  // Mode operations
  setReadOnly: (readOnly: boolean) => void;
  setDraggingState: (isDragging: boolean) => void;
  setConnectingState: (isConnecting: boolean) => void;
  
  // Modal operations
  openModal: (modal: 'apikeys' | 'execution' | 'settings' | 'person') => void;
  closeModal: (modal: 'apikeys' | 'execution' | 'settings' | 'person') => void;
  closeAllModals: () => void;
  
  // UI helpers
  isSelected: (id: SelectableID) => boolean;
  getSelectionBounds: () => { min: Vec2; max: Vec2 } | null;
}

export const createUISlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  UISlice
> = (set, get) => ({
  // Initialize UI state
  selectedId: null,
  selectedType: null,
  multiSelectedIds: new Set(),
  highlightedPersonId: null,
  
  activeView: 'diagram',
  activeCanvas: 'main',
  dashboardTab: 'properties',
  
  zoom: 1,
  position: { x: 0, y: 0 },
  
  readOnly: false,
  executionReadOnly: false,
  isDragging: false,
  isConnecting: false,
  
  showApiKeysModal: false,
  showExecutionModal: false,
  showSettingsModal: false,
  showPersonModal: false,
  
  // Selection operations
  select: (id, type) => set(state => {
    state.selectedId = id;
    state.selectedType = type;
    state.multiSelectedIds.clear();
    
    // Auto-switch dashboard tab based on selection
    if (type === 'person') {
      state.dashboardTab = 'persons';
    } else if (type === 'node' || type === 'arrow') {
      state.dashboardTab = 'properties';
    }
  }),
  
  multiSelect: (ids, type) => set(state => {
    state.selectedId = ids[0] || null;
    state.selectedType = type;
    state.multiSelectedIds = new Set(ids);
  }),
  
  toggleSelection: (id, type) => set(state => {
    if (state.multiSelectedIds.has(id)) {
      state.multiSelectedIds.delete(id);
      if (state.selectedId === id) {
        // Select next item if current was deselected
        const remaining = Array.from(state.multiSelectedIds);
        state.selectedId = remaining[0] || null;
        state.selectedType = remaining.length > 0 ? type : null;
      }
    } else {
      state.multiSelectedIds.add(id);
      if (!state.selectedId) {
        state.selectedId = id;
        state.selectedType = type;
      }
    }
  }),
  
  clearSelection: () => set(state => {
    state.selectedId = null;
    state.selectedType = null;
    state.multiSelectedIds.clear();
  }),
  
  selectAll: () => set(state => {
    const allNodeIds = Array.from(state.nodes.keys());
    state.multiSelectedIds = new Set(allNodeIds);
    state.selectedId = allNodeIds[0] || null;
    state.selectedType = allNodeIds.length > 0 ? 'node' : null;
  }),
  
  // Highlight operations
  highlightPerson: (personId) => set(state => {
    state.highlightedPersonId = personId;
  }),
  
  // View operations
  setActiveView: (view) => set(state => {
    state.activeView = view;
  }),
  
  setActiveCanvas: (canvas) => set(state => {
    state.activeCanvas = canvas;
  }),
  
  setDashboardTab: (tab) => set(state => {
    state.dashboardTab = tab;
  }),
  
  // Viewport operations
  setViewport: (zoom, position) => set(state => {
    state.zoom = zoom;
    state.position = position;
  }),
  
  setZoom: (zoom) => set(state => {
    state.zoom = zoom;
  }),
  
  setPosition: (position) => set(state => {
    state.position = position;
  }),
  
  // Mode operations
  setReadOnly: (readOnly) => set(state => {
    state.readOnly = readOnly;
  }),
  
  setDraggingState: (isDragging) => set(state => {
    state.isDragging = isDragging;
  }),
  
  setConnectingState: (isConnecting) => set(state => {
    state.isConnecting = isConnecting;
  }),
  
  // Modal operations
  openModal: (modal) => set(state => {
    switch (modal) {
      case 'apikeys':
        state.showApiKeysModal = true;
        break;
      case 'execution':
        state.showExecutionModal = true;
        break;
      case 'settings':
        state.showSettingsModal = true;
        break;
      case 'person':
        state.showPersonModal = true;
        break;
    }
  }),
  
  closeModal: (modal) => set(state => {
    switch (modal) {
      case 'apikeys':
        state.showApiKeysModal = false;
        break;
      case 'execution':
        state.showExecutionModal = false;
        break;
      case 'settings':
        state.showSettingsModal = false;
        break;
      case 'person':
        state.showPersonModal = false;
        break;
    }
  }),
  
  closeAllModals: () => set(state => {
    state.showApiKeysModal = false;
    state.showExecutionModal = false;
    state.showSettingsModal = false;
    state.showPersonModal = false;
  }),
  
  // UI helpers
  isSelected: (id) => {
    const state = get();
    return state.selectedId === id || state.multiSelectedIds.has(id);
  },
  
  getSelectionBounds: () => {
    const state = get();
    const selectedIds = state.multiSelectedIds.size > 0 
      ? Array.from(state.multiSelectedIds)
      : state.selectedId ? [state.selectedId] : [];
    
    if (selectedIds.length === 0) return null;
    
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    selectedIds.forEach(id => {
      const node = state.nodes.get(id as NodeID);
      if (node) {
        minX = Math.min(minX, node.position.x);
        minY = Math.min(minY, node.position.y);
        maxX = Math.max(maxX, node.position.x + 200); // Assume node width
        maxY = Math.max(maxY, node.position.y + 100); // Assume node height
      }
    });
    
    return {
      min: { x: minX, y: minY },
      max: { x: maxX, y: maxY }
    };
  }
});