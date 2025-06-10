/**
 * useStoreSelectors - Legacy store selector functions
 * 
 * This file contains utility functions for working with the unified store.
 * For new code, prefer using specific hooks like useExport for diagram operations.
 * 
 * The export/import functions here work with DomainDiagram format (Records),
 * while the new export system (useExport hook) works with ExportFormat (arrays with labels).
 */

import { useUnifiedStore } from '@/stores/useUnifiedStore';
import type { DomainNode, DomainArrow, DomainPerson, DomainHandle, DomainApiKey, DomainDiagram } from '@/types/domain';
import type { NodeID, ArrowID, PersonID, ApiKeyID, HandleID } from '@/types/branded';


export const useUIState = () => {
  const store = useUnifiedStore();
  
  return {
    dashboardTab: store.dashboardTab,
    setDashboardTab: store.setDashboardTab,
    activeCanvas: store.activeCanvas as 'main' | 'execution' | 'memory',
    setActiveCanvas: store.setActiveCanvas,
    toggleCanvas: () => {
      const canvases: ('main' | 'execution' | 'memory')[] = ['main', 'execution', 'memory'];
      const currentCanvas = store.activeCanvas || 'main';
      const currentIndex = canvases.indexOf(currentCanvas);
      const nextIndex = (currentIndex + 1) % canvases.length;
      store.setActiveCanvas(canvases[nextIndex] as 'main' | 'execution' | 'memory');
    },
    activeView: store.activeView,
    showApiKeysModal: store.showApiKeysModal,
    showExecutionModal: store.showExecutionModal,
    openApiKeysModal: store.openApiKeysModal,
    closeApiKeysModal: store.closeApiKeysModal,
    openExecutionModal: store.openExecutionModal,
    closeExecutionModal: store.closeExecutionModal,
    hasSelection: store.selectedId !== null,
  };
};



// Diagram export/import operations
// Note: These functions provide a simpler Record-based format for compatibility.
// For full export/import with label resolution, use the useExport hook instead.

export const exportDiagramState = (): DomainDiagram | null => {
  const state = useUnifiedStore.getState();
  
  if (state.nodes.size === 0) return null;
  
  // Convert Maps to Records - simple direct conversion
  const nodes: Record<NodeID, DomainNode> = {};
  const arrows: Record<ArrowID, DomainArrow> = {};
  const persons: Record<PersonID, DomainPerson> = {};
  const handles: Record<HandleID, DomainHandle> = {};
  const apiKeys: Record<ApiKeyID, DomainApiKey> = {};
  
  state.nodes.forEach((node, id) => { nodes[id] = node; });
  state.arrows.forEach((arrow, id) => { arrows[id] = arrow; });
  state.persons.forEach((person, id) => { persons[id] = person; });
  state.handles.forEach((handle, id) => { handles[id] = handle; });
  state.apiKeys.forEach((key, id) => { apiKeys[id] = key; });
  
  return {
    nodes,
    arrows,
    persons,
    handles,
    apiKeys,
  };
};

export const loadDiagram = (diagram: DomainDiagram) => {
  const state = useUnifiedStore.getState();
  
  state.transaction(() => {
    // Clear existing data
    state.nodes.clear();
    state.arrows.clear();
    state.handles.clear();
    state.persons.clear();
    state.apiKeys.clear();
    
    // Load new data from Records
    Object.entries(diagram.nodes).forEach(([id, node]) => state.nodes.set(id as NodeID, node));
    Object.entries(diagram.arrows).forEach(([id, arrow]) => state.arrows.set(id as ArrowID, arrow));
    Object.entries(diagram.handles).forEach(([id, handle]) => state.handles.set(id as HandleID, handle));
    Object.entries(diagram.persons).forEach(([id, person]) => state.persons.set(id as PersonID, person));
    if (diagram.apiKeys) {
      Object.entries(diagram.apiKeys).forEach(([id, key]) => state.apiKeys.set(id as ApiKeyID, key));
    }
  });
};

export const clearDiagram = () => {
  const state = useUnifiedStore.getState();
  
  state.transaction(() => {
    state.nodes.clear();
    state.arrows.clear();
    state.handles.clear();
    state.persons.clear();
    state.apiKeys.clear();
    state.clearSelection();
  });
};

