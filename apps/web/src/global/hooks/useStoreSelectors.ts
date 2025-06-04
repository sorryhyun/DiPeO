import React from 'react';
import { useNodeArrowStore, usePersonStore, useMonitorStore } from '@/global/stores';
import { useExecutionStore } from '@/global/stores/executionStore';
import { useConsolidatedUIStore } from '@/global/stores/consolidatedUIStore';

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
  return useNodeArrowStore(state => state.updateNodeData);
};

export const useArrowDataUpdater = () => {
  return useNodeArrowStore(state => state.updateArrowData);
};

// Canvas state - combines multiple related selectors with monitor support
export const useCanvasState = () => {
  const isMonitorMode = useMonitorStore(state => state.isMonitorMode);
  const monitorNodes = useMonitorStore(state => state.monitorNodes);
  const monitorArrows = useMonitorStore(state => state.monitorArrows);
  const regularNodes = useNodeArrowStore(state => state.nodes);
  const regularArrows = useNodeArrowStore(state => state.arrows);
  const nodes = isMonitorMode ? monitorNodes : regularNodes;
  const arrows = isMonitorMode ? monitorArrows : regularArrows;
  const onNodesChange = useNodeArrowStore(state => state.onNodesChange);
  const onArrowsChange = useNodeArrowStore(state => state.onArrowsChange);
  const onConnect = useNodeArrowStore(state => state.onConnect);
  const addNode = useNodeArrowStore(state => state.addNode);
  const deleteNode = useNodeArrowStore(state => state.deleteNode);
  const deleteArrow = useNodeArrowStore(state => state.deleteArrow);
  
  // Memoize functions and object to prevent unnecessary re-renders
  return React.useMemo(() => ({
    nodes,
    arrows,
    isMonitorMode,
    onNodesChange,
    onArrowsChange,
    onConnect,
    addNode,
    deleteNode,
    deleteArrow,
  }), [nodes, arrows, isMonitorMode, onNodesChange, onArrowsChange, onConnect, addNode, deleteNode, deleteArrow]);
};

// Person operations with monitor support
export const usePersons = () => {
  const isMonitorMode = useMonitorStore(state => state.isMonitorMode);
  const monitorPersons = useMonitorStore(state => state.monitorPersons);
  const regularPersons = usePersonStore(state => state.persons);
  const persons = isMonitorMode ? monitorPersons : regularPersons;
  const addPerson = usePersonStore(state => state.addPerson);
  const updatePerson = usePersonStore(state => state.updatePerson);
  const deletePerson = usePersonStore(state => state.deletePerson);
  const getPersonById = usePersonStore(state => state.getPersonById);
  
  return React.useMemo(() => ({
    persons,
    isMonitorMode,
    addPerson,
    updatePerson,
    deletePerson,
    getPersonById,
  }), [persons, isMonitorMode, addPerson, updatePerson, deletePerson, getPersonById]);
};

// Node operations with monitor support
export const useNodes = () => {
  const isMonitorMode = useMonitorStore(state => state.isMonitorMode);
  const monitorNodes = useMonitorStore(state => state.monitorNodes);
  const regularNodes = useNodeArrowStore(state => state.nodes);
  const nodes = isMonitorMode ? monitorNodes : regularNodes;
  const onNodesChange = useNodeArrowStore(state => state.onNodesChange);
  const addNode = useNodeArrowStore(state => state.addNode);
  const deleteNode = useNodeArrowStore(state => state.deleteNode);
  
  return {
    nodes,
    isMonitorMode,
    onNodesChange,
    addNode,
    deleteNode,
  };
};

// Arrow operations with monitor support
export const useArrows = () => {
  const isMonitorMode = useMonitorStore(state => state.isMonitorMode);
  const monitorArrows = useMonitorStore(state => state.monitorArrows);
  const regularArrows = useNodeArrowStore(state => state.arrows);
  const arrows = isMonitorMode ? monitorArrows : regularArrows;
  const onArrowsChange = useNodeArrowStore(state => state.onArrowsChange);
  const onConnect = useNodeArrowStore(state => state.onConnect);
  const deleteArrow = useNodeArrowStore(state => state.deleteArrow);
  
  return {
    arrows,
    isMonitorMode,
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
  
  const hasSelection = useConsolidatedUIStore(state => state.hasSelection);
  
  return {
    dashboardTab,
    setDashboardTab,
    activeCanvas,
    setActiveCanvas,
    toggleCanvas,
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