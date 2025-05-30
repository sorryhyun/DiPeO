import React from 'react';
import { useConsolidatedDiagramStore } from '@/stores/consolidatedDiagramStore';
import { useExecutionStore } from '@/stores/executionStore';

// ===== Key Optimized Selectors =====

// Re-export node hooks from features
export { useNodeExecutionState, useNodeDataUpdater, useNodes } from '@/features/nodes/hooks/useNodeOperations';

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

// Re-export layout hooks from features
export { useUIState, useSelectedElement } from '@/features/layout/hooks/useLayoutState';

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