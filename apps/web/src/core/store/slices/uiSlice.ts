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
  isMonitorMode: boolean;
  
  // NOTE: Modal state has been moved to local component state
  // to reduce global store complexity
  
  // NOTE: Canvas settings (showGrid, showMinimap, showDebugInfo) and
  // temporary states (isDragging, isConnecting) have been moved to local
  // component state to reduce global store complexity
  
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
  setCanvasMode: (mode: CanvasMode) => void;
  setMonitorMode: (isMonitorMode: boolean) => void;
  
  // Clear operation
  clearUIState: () => void;
  
  // NOTE: Modal operations removed - use local component state instead
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
  isMonitorMode: false,
  
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
  
  setCanvasMode: (mode) => set(state => {
    state.canvasMode = mode;
  }),
  
  setMonitorMode: (isMonitorMode) => set(state => {
    state.isMonitorMode = isMonitorMode;
    // When entering monitor mode, automatically set read-only
    if (isMonitorMode) {
      state.readOnly = true;
    }
  }),
  
  // Clear operation
  clearUIState: () => set(state => {
    // Reset selection state
    state.selectedId = null;
    state.selectedType = null;
    state.multiSelectedIds.clear();
    state.highlightedPersonId = null;
    
    // Reset view state to defaults
    state.activeView = 'diagram';
    state.activeCanvas = 'main';
    state.dashboardTab = 'properties';
    
    // Reset viewport state
    state.zoom = 1;
    state.position = { x: 0, y: 0 };
    
    // Reset mode state
    state.readOnly = false;
    state.executionReadOnly = false;
    state.isMonitorMode = false;
    state.canvasMode = 'select';
  }),
  
});