import React from 'react';
import { useDiagramStore } from '@/stores';

export const useCanvasSelectors = () => {
  const nodes = useDiagramStore(state => state.nodes);
  const arrows = useDiagramStore(state => state.arrows);
  const persons = useDiagramStore(state => state.persons);
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  
  // Canvas operations
  const onNodesChange = useDiagramStore(state => state.onNodesChange);
  const onArrowsChange = useDiagramStore(state => state.onArrowsChange);
  const onConnect = useDiagramStore(state => state.onConnect);
  
  // Node operations
  const addNode = useDiagramStore(state => state.addNode);
  const updateNode = useDiagramStore(state => state.updateNode);
  const deleteNode = useDiagramStore(state => state.deleteNode);
  
  // Arrow operations
  const updateArrow = useDiagramStore(state => state.updateArrow);
  const deleteArrow = useDiagramStore(state => state.deleteArrow);
  
  // Person operations
  const addPerson = useDiagramStore(state => state.addPerson);
  const updatePerson = useDiagramStore(state => state.updatePerson);
  const deletePerson = useDiagramStore(state => state.deletePerson);
  const getPersonById = useDiagramStore(state => state.getPersonById);
  
  // Diagram operations
  const loadDiagram = useDiagramStore(state => state.loadDiagram);
  const exportDiagram = useDiagramStore(state => state.exportDiagram);
  const clear = useDiagramStore(state => state.clear);
  
  return React.useMemo(() => ({
    // Data
    nodes,
    arrows,
    persons,
    isMonitorMode: isReadOnly,
    
    // Canvas operations
    onNodesChange,
    onArrowsChange,
    onConnect,
    
    // Node operations
    addNode,
    updateNode,
    deleteNode,
    
    // Arrow operations
    updateArrow,
    deleteArrow,
    
    // Person operations
    addPerson,
    updatePerson,
    deletePerson,
    getPersonById,
    
    // Diagram operations
    loadDiagram,
    exportDiagram,
    clear,
  }), [
    nodes, arrows, persons, isReadOnly,
    onNodesChange, onArrowsChange, onConnect,
    addNode, updateNode, deleteNode,
    updateArrow, deleteArrow,
    addPerson, updatePerson, deletePerson, getPersonById,
    loadDiagram, exportDiagram, clear
  ]);
};

// Specific node state selector for performance
export const useNodeExecutionState = (nodeId: string) => {
  // This is kept here as it's canvas-specific and performance-critical
  return useDiagramStore(state => ({
    node: state.nodes.find(n => n.id === nodeId),
    isReadOnly: state.isReadOnly,
  }));
};