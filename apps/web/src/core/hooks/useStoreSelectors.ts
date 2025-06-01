import React from 'react';
import { useConsolidatedDiagramStore } from '@/core/stores/consolidatedDiagramStore';
import { useExecutionStore } from '@/core/stores/executionStore';
import { useConsolidatedUIStore } from '@/core/stores/consolidatedUIStore';

// ===== Key Optimized Selectors =====

// Execution state for specific node - avoids subscribing to entire execution store
export const useNodeExecutionState = (nodeId: string) => {
  const isRunning = useExecutionStore(state => state.runningNodes.includes(nodeId));
  const isCurrentRunning = useExecutionStore(state => state.currentRunningNode === nodeId);
  const nodeRunningState = useExecutionStore(state => state.nodeRunningStates[nodeId] || false);
  
  // Memoize the return object to prevent unnecessary re-renders
  return React.useMemo(() => ({
    isRunning,
    isCurrentRunning,
    nodeRunningState,
  }), [isRunning, isCurrentRunning, nodeRunningState]);
};

// Single function selectors for common operations to avoid re-renders
export const useNodeDataUpdater = () => {
  return useConsolidatedDiagramStore(state => state.updateNodeData);
};

export const useArrowDataUpdater = () => {
  return useConsolidatedDiagramStore(state => state.updateArrowData);
};

// Canvas state - combines multiple related selectors
export const useCanvasState = () => {
  const nodes = useConsolidatedDiagramStore(state => state.nodes);
  const arrows = useConsolidatedDiagramStore(state => state.arrows);
  const onNodesChange = useConsolidatedDiagramStore(state => state.onNodesChange);
  const onArrowsChange = useConsolidatedDiagramStore(state => state.onArrowsChange);
  const onConnect = useConsolidatedDiagramStore(state => state.onConnect);
  const addNode = useConsolidatedDiagramStore(state => state.addNode);
  const deleteNode = useConsolidatedDiagramStore(state => state.deleteNode);
  const deleteArrow = useConsolidatedDiagramStore(state => state.deleteArrow);
  
  // Memoize functions and object to prevent unnecessary re-renders
  return React.useMemo(() => ({
    nodes,
    arrows,
    onNodesChange,
    onArrowsChange,
    onConnect,
    addNode,
    deleteNode,
    deleteArrow,
  }), [nodes, arrows, onNodesChange, onArrowsChange, onConnect, addNode, deleteNode, deleteArrow]);
};

// Person operations
export const usePersons = () => {
  const persons = useConsolidatedDiagramStore(state => state.persons);
  const addPerson = useConsolidatedDiagramStore(state => state.addPerson);
  const updatePerson = useConsolidatedDiagramStore(state => state.updatePerson);
  const deletePerson = useConsolidatedDiagramStore(state => state.deletePerson);
  const getPersonById = useConsolidatedDiagramStore(state => state.getPersonById);
  
  return React.useMemo(() => ({
    persons,
    addPerson,
    updatePerson,
    deletePerson,
    getPersonById,
  }), [persons, addPerson, updatePerson, deletePerson, getPersonById]);
};

// Node operations
export const useNodes = () => {
  const nodes = useConsolidatedDiagramStore(state => state.nodes);
  const onNodesChange = useConsolidatedDiagramStore(state => state.onNodesChange);
  const addNode = useConsolidatedDiagramStore(state => state.addNode);
  const deleteNode = useConsolidatedDiagramStore(state => state.deleteNode);
  
  return {
    nodes,
    onNodesChange,
    addNode,
    deleteNode,
  };
};

// Arrow operations
export const useArrows = () => {
  const arrows = useConsolidatedDiagramStore(state => state.arrows);
  const onArrowsChange = useConsolidatedDiagramStore(state => state.onArrowsChange);
  const onConnect = useConsolidatedDiagramStore(state => state.onConnect);
  const deleteArrow = useConsolidatedDiagramStore(state => state.deleteArrow);
  
  return {
    arrows,
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