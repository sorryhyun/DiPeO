import React from 'react';
import { useConsolidatedUIStore } from '@/stores/consolidatedUIStore';

export const useUISelectors = () => {
  // Selection state
  const selectedNodeId = useConsolidatedUIStore(state => state.selectedNodeId);
  const selectedArrowId = useConsolidatedUIStore(state => state.selectedArrowId);
  const selectedPersonId = useConsolidatedUIStore(state => state.selectedPersonId);
  const hasSelection = useConsolidatedUIStore(state => state.hasSelection);
  
  // Dashboard state
  const dashboardTab = useConsolidatedUIStore(state => state.dashboardTab);
  
  // Canvas state
  const activeCanvas = useConsolidatedUIStore(state => state.activeCanvas);
  const activeView = useConsolidatedUIStore(state => state.activeView);
  
  // Modal state
  const showApiKeysModal = useConsolidatedUIStore(state => state.showApiKeysModal);
  const showExecutionModal = useConsolidatedUIStore(state => state.showExecutionModal);
  
  // Actions
  const setSelectedNodeId = useConsolidatedUIStore(state => state.setSelectedNodeId);
  const setSelectedArrowId = useConsolidatedUIStore(state => state.setSelectedArrowId);
  const setSelectedPersonId = useConsolidatedUIStore(state => state.setSelectedPersonId);
  const clearSelection = useConsolidatedUIStore(state => state.clearSelection);
  
  const setDashboardTab = useConsolidatedUIStore(state => state.setDashboardTab);
  const setActiveCanvas = useConsolidatedUIStore(state => state.setActiveCanvas);
  const setActiveView = useConsolidatedUIStore(state => state.setActiveView);
  const toggleCanvas = useConsolidatedUIStore(state => state.toggleCanvas);
  
  const openApiKeysModal = useConsolidatedUIStore(state => state.openApiKeysModal);
  const closeApiKeysModal = useConsolidatedUIStore(state => state.closeApiKeysModal);
  const openExecutionModal = useConsolidatedUIStore(state => state.openExecutionModal);
  const closeExecutionModal = useConsolidatedUIStore(state => state.closeExecutionModal);
  
  return React.useMemo(() => ({
    // Selection
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection,
    setSelectedNodeId,
    setSelectedArrowId,
    setSelectedPersonId,
    clearSelection,
    
    // Dashboard
    dashboardTab,
    setDashboardTab,
    
    // Canvas
    activeCanvas,
    activeView,
    setActiveCanvas,
    setActiveView,
    toggleCanvas,
    
    // Modals
    showApiKeysModal,
    showExecutionModal,
    openApiKeysModal,
    closeApiKeysModal,
    openExecutionModal,
    closeExecutionModal,
  }), [
    selectedNodeId, selectedArrowId, selectedPersonId, hasSelection,
    setSelectedNodeId, setSelectedArrowId, setSelectedPersonId, clearSelection,
    dashboardTab, setDashboardTab,
    activeCanvas, activeView, setActiveCanvas, setActiveView, toggleCanvas,
    showApiKeysModal, showExecutionModal,
    openApiKeysModal, closeApiKeysModal, openExecutionModal, closeExecutionModal
  ]);
};

// Specific selection hooks for performance
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