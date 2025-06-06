import React from 'react';
import { useDiagramStore } from '@/stores';
import { useExecutionStore } from '@/stores/executionStore';
import { useConsolidatedUIStore } from '@/stores/consolidatedUIStore';
import { useHistoryStore } from '@/stores/historyStore';
import { useApiKeyStore } from '@/stores/apiKeyStore';

// ===== Key Optimized Selectors =====

// Execution state for specific node - avoids subscribing to entire execution store
export const useNodeExecutionState = (nodeId: string) => {
  // Subscribe to lastUpdate to force re-renders when execution state changes
  const lastUpdate = useExecutionStore(state => state.lastUpdate);
  const runningNodes = useExecutionStore(state => state.runningNodes);
  const isRunning = runningNodes.includes(nodeId);
  const isCurrentRunning = useExecutionStore(state => state.currentRunningNode === nodeId);
  const nodeRunningState = useExecutionStore(state => state.nodeRunningStates[nodeId] || false);
  const skippedNodeInfo = useExecutionStore(state => state.skippedNodes[nodeId]);
  const isSkipped = Boolean(skippedNodeInfo);
  
  // Debug logging for node execution state
  React.useEffect(() => {
    if (isRunning || nodeRunningState || isSkipped) {
      console.log(`[useNodeExecutionState] Node ${nodeId} state:`, {
        nodeId,
        isRunning,
        isCurrentRunning,
        nodeRunningState,
        isSkipped,
        skipReason: skippedNodeInfo?.reason,
        runningNodes,
        lastUpdate
      });
    }
  }, [nodeId, isRunning, isCurrentRunning, nodeRunningState, isSkipped, skippedNodeInfo, runningNodes, lastUpdate]);
  
  // Memoize the return object to prevent unnecessary re-renders
  return React.useMemo(() => ({
    isRunning,
    isCurrentRunning,
    nodeRunningState,
    isSkipped,
    skipReason: skippedNodeInfo?.reason,
  }), [isRunning, isCurrentRunning, nodeRunningState, isSkipped, skippedNodeInfo?.reason, lastUpdate]);
};

// Single function selectors for common operations to avoid re-renders
export const useNodeDataUpdater = () => {
  return useDiagramStore(state => state.updateNode);
};

export const useArrowDataUpdater = () => {
  return useDiagramStore(state => state.updateArrow);
};

// Canvas state - combines multiple related selectors with monitor support
export const useCanvasState = () => {
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  const nodes = useDiagramStore(state => state.nodes);
  const arrows = useDiagramStore(state => state.arrows);
  const onNodesChange = useDiagramStore(state => state.onNodesChange);
  const onArrowsChange = useDiagramStore(state => state.onArrowsChange);
  const onConnect = useDiagramStore(state => state.onConnect);
  const addNode = useDiagramStore(state => state.addNode);
  const deleteNode = useDiagramStore(state => state.deleteNode);
  const deleteArrow = useDiagramStore(state => state.deleteArrow);
  
  // Memoize functions and object to prevent unnecessary re-renders
  return React.useMemo(() => ({
    nodes,
    arrows,
    isMonitorMode: isReadOnly,
    onNodesChange,
    onArrowsChange,
    onConnect,
    addNode,
    deleteNode,
    deleteArrow,
  }), [nodes, arrows, isReadOnly, onNodesChange, onArrowsChange, onConnect, addNode, deleteNode, deleteArrow]);
};

// Person operations with monitor support
export const usePersons = () => {
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  const persons = useDiagramStore(state => state.persons);
  const addPerson = useDiagramStore(state => state.addPerson);
  const updatePerson = useDiagramStore(state => state.updatePerson);
  const deletePerson = useDiagramStore(state => state.deletePerson);
  const getPersonById = useDiagramStore(state => state.getPersonById);
  
  return React.useMemo(() => ({
    persons,
    isMonitorMode: isReadOnly,
    addPerson,
    updatePerson,
    deletePerson,
    getPersonById,
  }), [persons, isReadOnly, addPerson, updatePerson, deletePerson, getPersonById]);
};

// Node operations with monitor support
export const useNodes = () => {
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  const nodes = useDiagramStore(state => state.nodes);
  const onNodesChange = useDiagramStore(state => state.onNodesChange);
  const addNode = useDiagramStore(state => state.addNode);
  const deleteNode = useDiagramStore(state => state.deleteNode);
  
  return {
    nodes,
    isMonitorMode: isReadOnly,
    onNodesChange,
    addNode,
    deleteNode,
  };
};

// Arrow operations with monitor support
export const useArrows = () => {
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  const arrows = useDiagramStore(state => state.arrows);
  const onArrowsChange = useDiagramStore(state => state.onArrowsChange);
  const onConnect = useDiagramStore(state => state.onConnect);
  const deleteArrow = useDiagramStore(state => state.deleteArrow);
  
  return {
    arrows,
    isMonitorMode: isReadOnly,
    onArrowsChange,
    onConnect,
    deleteArrow,
  };
};

// UI state selectors
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

export const useUIState = () => {
  const dashboardTab = useConsolidatedUIStore(state => state.dashboardTab);
  const setDashboardTab = useConsolidatedUIStore(state => state.setDashboardTab);
  
  // Canvas state
  const activeCanvas = useConsolidatedUIStore(state => state.activeCanvas);
  const setActiveCanvas = useConsolidatedUIStore(state => state.setActiveCanvas);
  const toggleCanvas = useConsolidatedUIStore(state => state.toggleCanvas);
  
  // View state
  const activeView = useConsolidatedUIStore(state => state.activeView);
  const setActiveView = useConsolidatedUIStore(state => state.setActiveView);
  
  // Modal state
  const showApiKeysModal = useConsolidatedUIStore(state => state.showApiKeysModal);
  const showExecutionModal = useConsolidatedUIStore(state => state.showExecutionModal);
  const openApiKeysModal = useConsolidatedUIStore(state => state.openApiKeysModal);
  const closeApiKeysModal = useConsolidatedUIStore(state => state.closeApiKeysModal);
  const openExecutionModal = useConsolidatedUIStore(state => state.openExecutionModal);
  const closeExecutionModal = useConsolidatedUIStore(state => state.closeExecutionModal);
  
  const hasSelection = useConsolidatedUIStore(state => state.hasSelection);
  
  return {
    dashboardTab,
    setDashboardTab,
    activeCanvas,
    setActiveCanvas,
    toggleCanvas,
    activeView,
    setActiveView,
    showApiKeysModal,
    showExecutionModal,
    openApiKeysModal,
    closeApiKeysModal,
    openExecutionModal,
    closeExecutionModal,
    hasSelection,
  };
};

// Execution status
export const useExecutionStatus = () => {
  const runContext = useExecutionStore(state => state.runContext);
  const runningNodes = useExecutionStore(state => state.runningNodes);
  const currentRunningNode = useExecutionStore(state => state.currentRunningNode);
  const nodeRunningStates = useExecutionStore(state => state.nodeRunningStates);
  
  return {
    runContext,
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
  };
};

// Missing exports for backward compatibility
export const getApiKeys = () => useApiKeyStore.getState().apiKeys;

// History actions
export const useUndo = () => useHistoryStore(state => state.undo);
export const useRedo = () => useHistoryStore(state => state.redo);
export const useCanUndo = () => useHistoryStore(state => state.canUndo);
export const useCanRedo = () => useHistoryStore(state => state.canRedo);

// Execution actions  
export const useAddRunningNode = () => useExecutionStore(state => state.addRunningNode);
export const useRemoveRunningNode = () => useExecutionStore(state => state.removeRunningNode);
export const useSetCurrentRunningNode = () => useExecutionStore(state => state.setCurrentRunningNode);
export const useSetRunContext = () => useExecutionStore(state => state.setRunContext);
export const useAddSkippedNode = () => useExecutionStore(state => state.addSkippedNode);

// Diagram actions
export const useLoadDiagram = () => useDiagramStore(state => state.loadDiagram);
export const exportDiagramState = () => useDiagramStore.getState().exportDiagram();

// More store selectors
export const useSkippedNodes = () => useExecutionStore(state => state.skippedNodes);
export const useExecutions = () => useExecutionStore(state => state);
export const clearDiagram = () => useDiagramStore.getState().clear();

// Missing exports for compatibility
export const loadDiagram = (diagram: any) => useDiagramStore.getState().loadDiagram(diagram);
export const useSelectedPersonId = () => useConsolidatedUIStore(state => state.selectedPersonId);
export const useSetSelectedPersonId = () => useConsolidatedUIStore(state => state.setSelectedPersonId);
export const useClearRunContext = () => {
  const setRunContext = useExecutionStore(state => state.setRunContext);
  return () => setRunContext({});
};
export const useClearRunningNodes = () => {
  const store = useExecutionStore.getState();
  return () => {
    store.runningNodes.forEach(nodeId => store.removeRunningNode(nodeId));
    store.setCurrentRunningNode(null);
  };
};

// Missing exports for backward compatibility
export const useUpdateNodeData = () => useDiagramStore(state => state.updateNode);
export const useUpdateArrowData = () => useDiagramStore(state => state.updateArrow);
export const useUpdatePerson = () => useDiagramStore(state => state.updatePerson);

// Grouped selectors for compatibility
export const useUISelectors = () => {
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

export const useCanvasSelectors = () => {
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  const nodes = useDiagramStore(state => state.nodes);
  const arrows = useDiagramStore(state => state.arrows);
  const onNodesChange = useDiagramStore(state => state.onNodesChange);
  const onArrowsChange = useDiagramStore(state => state.onArrowsChange);
  const onConnect = useDiagramStore(state => state.onConnect);
  const addNode = useDiagramStore(state => state.addNode);
  const deleteNode = useDiagramStore(state => state.deleteNode);
  const deleteArrow = useDiagramStore(state => state.deleteArrow);
  const updateNode = useDiagramStore(state => state.updateNode);
  
  return {
    nodes,
    arrows,
    isMonitorMode: isReadOnly,
    onNodesChange,
    onArrowsChange,
    onConnect,
    addNode,
    deleteNode,
    deleteArrow,
    updateNode,
  };
};

export const useExecutionSelectors = () => {
  const runContext = useExecutionStore(state => state.runContext);
  const runningNodes = useExecutionStore(state => state.runningNodes);
  const currentRunningNode = useExecutionStore(state => state.currentRunningNode);
  const nodeRunningStates = useExecutionStore(state => state.nodeRunningStates);
  const skippedNodes = useExecutionStore(state => state.skippedNodes);
  
  return {
    runContext,
    runningNodes,
    currentRunningNode,
    nodeRunningStates,
    skippedNodes,
  };
};

export const useHistorySelectors = () => {
  const undo = useHistoryStore(state => state.undo);
  const redo = useHistoryStore(state => state.redo);
  const canUndo = useHistoryStore(state => state.canUndo);
  const canRedo = useHistoryStore(state => state.canRedo);
  
  return {
    undo,
    redo,
    canUndo,
    canRedo,
  };
};