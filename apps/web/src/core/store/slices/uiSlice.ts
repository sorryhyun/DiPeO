import { StateCreator } from 'zustand';
import { ArrowID, NodeID, PersonID } from '@/core/types';
import { Vec2 } from '@dipeo/domain-models';
import { UnifiedStore } from '../unifiedStore.types';

export type SelectableID = NodeID | ArrowID | PersonID;
export type SelectableType = 'node' | 'arrow' | 'person';
export type ActiveView = 'diagram' | 'execution' | 'persons' | 'apikeys';
export type ActiveCanvas = 'main' | 'execution' | 'memory' | 'preview' | 'monitor';
export type DashboardTab = 'properties' | 'persons' | 'settings' | 'history';
export type CanvasMode = 'select' | 'pan' | 'zoom';

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
  isMonitorMode: boolean;
  
  // Modal state
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  showSettingsModal: boolean;
  showPersonModal: boolean;
  activeModal: string | null;
  
  // Canvas settings
  showGrid: boolean;
  showMinimap: boolean;
  showDebugInfo: boolean;
  canvasMode: CanvasMode;
  
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
  setCanvasMode: (mode: CanvasMode) => void;
  
  // Canvas settings operations
  setShowGrid: (show: boolean) => void;
  setShowMinimap: (show: boolean) => void;
  setShowDebugInfo: (show: boolean) => void;
  
  // Modal operations
  openModal: (modal: 'apikeys' | 'execution' | 'settings' | 'person') => void;
  closeModal: (modal: 'apikeys' | 'execution' | 'settings' | 'person') => void;
  closeAllModals: () => void;
}

// Helper to auto-switch dashboard tab based on selection
const autoSwitchTab = (state: UnifiedStore, type: SelectableType | null) => {
  if (type === 'person') {
    state.dashboardTab = 'persons';
  } else if (type === 'node' || type === 'arrow') {
    state.dashboardTab = 'properties';
  }
};

export const createUISlice: StateCreator<
  UnifiedStore,
  [['zustand/immer', never]],
  [],
  UISlice
> = (set, _get) => ({
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
  isMonitorMode: false,
  
  showApiKeysModal: false,
  showExecutionModal: false,
  showSettingsModal: false,
  showPersonModal: false,
  activeModal: null,
  
  showGrid: true,
  showMinimap: false,
  showDebugInfo: false,
  canvasMode: 'select',
  
  // Selection operations
  select: (id, type) => set(state => {
    state.selectedId = id;
    state.selectedType = type;
    state.multiSelectedIds.clear();
    autoSwitchTab(state, type);
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
  
  setCanvasMode: (mode) => set(state => {
    state.canvasMode = mode;
  }),
  
  // Canvas settings operations
  setShowGrid: (show) => set(state => {
    state.showGrid = show;
  }),
  
  setShowMinimap: (show) => set(state => {
    state.showMinimap = show;
  }),
  
  setShowDebugInfo: (show) => set(state => {
    state.showDebugInfo = show;
  }),
  
  // Modal operations
  openModal: (modal) => set(state => {
    state.activeModal = modal;
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
    if (state.activeModal === modal) {
      state.activeModal = null;
    }
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
    state.activeModal = null;
    state.showApiKeysModal = false;
    state.showExecutionModal = false;
    state.showSettingsModal = false;
    state.showPersonModal = false;
  })
});