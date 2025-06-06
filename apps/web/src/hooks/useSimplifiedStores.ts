import { useDiagramStore, useExecutionStore, useUIStore } from '../stores';

// Simplified hook for diagram data and actions
export const useDiagram = () => {
  const {
    // Data
    nodes,
    arrows,
    persons,
    apiKeys,
    
    // Node actions
    addNode,
    updateNode,
    deleteNode,
    
    // Arrow actions
    addArrow,
    updateArrow,
    deleteArrow,
    
    // Person actions
    addPerson,
    updatePerson,
    deletePerson,
    getPersonById,
    
    // API Key actions
    addApiKey,
    updateApiKey,
    deleteApiKey,
    getApiKeyById,
    setApiKeys,
    
    // Batch operations
    setNodes,
    setArrows,
    setPersons,
    
    // Utility
    clear,
    loadDiagram,
    exportDiagram
  } = useDiagramStore();
  
  return {
    // Data
    nodes,
    arrows,
    persons,
    apiKeys,
    
    // Actions
    addNode,
    updateNode,
    deleteNode,
    addArrow,
    updateArrow,
    deleteArrow,
    addPerson,
    updatePerson,
    deletePerson,
    getPersonById,
    addApiKey,
    updateApiKey,
    deleteApiKey,
    getApiKeyById,
    setApiKeys,
    
    // Batch
    setNodes,
    setArrows,
    setPersons,
    
    // Utility
    clear,
    loadDiagram,
    exportDiagram
  };
};

// Simplified hook for execution state and control
export const useExecution = () => {
  const {
    // Status
    isExecuting,
    executionId,
    
    // Node tracking
    currentRunningNode,
    runningNodes,
    nodeRunningStates,
    skippedNodes,
    nodeErrors,
    
    // Context
    runContext,
    lastUpdate,
    
    // Actions
    startExecution,
    stopExecution,
    reset,
    
    // Node management
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    addSkippedNode,
    setNodeError,
    
    // Context
    setRunContext,
    
    // Getters
    isNodeRunning,
    hasNodeError,
    getNodeError
  } = useExecutionStore();
  
  return {
    // Status
    status: isExecuting ? 'running' : 'idle',
    isExecuting,
    executionId,
    
    // Node state
    currentRunningNode,
    runningNodes,
    nodeRunningStates,
    skippedNodes,
    nodeErrors,
    
    // Context
    runContext,
    lastUpdate,
    
    // Control
    execute: startExecution,
    stop: stopExecution,
    reset,
    
    // Node control
    addRunningNode,
    removeRunningNode,
    setCurrentRunningNode,
    addSkippedNode,
    setNodeError,
    setRunContext,
    
    // Utils
    isNodeRunning,
    hasNodeError,
    getNodeError
  };
};

// Simplified hook for UI state and navigation
export const useUI = () => {
  const {
    // Selection
    selection,
    
    // Views
    activeView,
    activeCanvas,
    dashboardTab,
    
    // Modals
    showApiKeysModal,
    showExecutionModal,
    
    // Selection actions
    select,
    clearSelection,
    
    // View actions
    setActiveView,
    setActiveCanvas,
    toggleCanvas,
    setDashboardTab,
    
    // Modal actions
    openApiKeysModal,
    closeApiKeysModal,
    openExecutionModal,
    closeExecutionModal,
    
    // Getters
    hasSelection,
    getSelectedId,
    getSelectedType
  } = useUIStore();
  
  return {
    // Selection
    selected: selection,
    selectedId: getSelectedId(),
    selectedType: getSelectedType(),
    hasSelection: hasSelection(),
    
    // Views
    activeView,
    activeCanvas,
    dashboardTab,
    
    // Modals
    modals: {
      apiKeys: showApiKeysModal,
      execution: showExecutionModal
    },
    
    // Actions
    select,
    clearSelection,
    setView: setActiveView,
    setCanvas: setActiveCanvas,
    toggleCanvas,
    setTab: setDashboardTab,
    
    // Modal actions
    openModal: {
      apiKeys: openApiKeysModal,
      execution: openExecutionModal
    },
    closeModal: {
      apiKeys: closeApiKeysModal,
      execution: closeExecutionModal
    }
  };
};