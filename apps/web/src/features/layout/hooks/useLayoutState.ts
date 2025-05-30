import { useConsolidatedUIStore } from '@/shared/stores/consolidatedUIStore';

// Layout and UI state management
export const useUIState = () => {
  const dashboardTab = useConsolidatedUIStore(state => state.dashboardTab);
  const setDashboardTab = useConsolidatedUIStore(state => state.setDashboardTab);
  const isMemoryLayerTilted = useConsolidatedUIStore(state => state.isMemoryLayerTilted);
  const setMemoryLayerTilted = useConsolidatedUIStore(state => state.setMemoryLayerTilted);
  const toggleMemoryLayer = useConsolidatedUIStore(state => state.toggleMemoryLayer);
  const hasSelection = useConsolidatedUIStore(state => state.hasSelection);
  
  return {
    dashboardTab,
    setDashboardTab,
    isMemoryLayerTilted,
    setMemoryLayerTilted,
    toggleMemoryLayer,
    hasSelection,
  };
};

// Element selection state - can be used by both layout and properties
export const useSelectedElement = () => {
  const selectedNodeId = useConsolidatedUIStore(state => state.selectedNodeId);
  const selectedArrowId = useConsolidatedUIStore(state => state.selectedArrowId);
  const selectedPersonId = useConsolidatedUIStore(state => state.selectedPersonId);
  const setSelectedNodeId = useConsolidatedUIStore(state => state.setSelectedNodeId);
  const setSelectedArrowId = useConsolidatedUIStore(state => state.setSelectedArrowId);
  const setSelectedPersonId = useConsolidatedUIStore(state => state.setSelectedPersonId);
  const clearSelection = useConsolidatedUIStore(state => state.clearSelection);
  
  return {
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    setSelectedNodeId,
    setSelectedArrowId,
    setSelectedPersonId,
    clearSelection,
  };
};