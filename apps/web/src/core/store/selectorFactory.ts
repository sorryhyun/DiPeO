import type { UnifiedStore } from './unifiedStore.types';



export const createCommonStoreSelector = () => (state: UnifiedStore) => ({
  nodes: state.nodes,
  nodesMap: state.nodes,
  handles: state.handles,
  handlesMap: state.handles,
  arrows: state.arrows,
  persons: state.persons,
  
  nodesArray: state.nodesArray,
  arrowsArray: state.arrowsArray,
  personsArray: state.personsArray,
  
  dataVersion: state.dataVersion,
  
  isMonitorMode: state.readOnly,
  isExecutionMode: state.executionReadOnly,
  
  selectedId: state.selectedId,
  selectedType: state.selectedType,
  
  executionId: state.execution.id,
  isRunning: state.execution.isRunning,
  runningNodes: state.execution.runningNodes,
  nodeStates: state.execution.nodeStates,
  context: state.execution.context,
  
  canUndo: state.history.undoStack.length > 0,
  canRedo: state.history.redoStack.length > 0,
  
  addNode: state.addNode,
  updateNode: state.updateNode,
  deleteNode: state.deleteNode,
  updateNodeSilently: state.updateNodeSilently,

  addArrow: state.addArrow,
  updateArrow: state.updateArrow,
  deleteArrow: state.deleteArrow,
  
  addPerson: state.addPerson,
  updatePerson: state.updatePerson,
  deletePerson: state.deletePerson,
  
  select: state.select,
  clearSelection: state.clearSelection,
  
  startExecution: state.startExecution,
  updateNodeExecution: state.updateNodeExecution,
  stopExecution: state.stopExecution,
  
  transaction: state.transaction,
  undo: state.undo,
  redo: state.redo,
});

export const createSubsetSelector = <T extends keyof ReturnType<ReturnType<typeof createCommonStoreSelector>>>(
  keys: T[]
) => {
  const commonSelector = createCommonStoreSelector();
  
  return (state: UnifiedStore) => {
    const fullSelection = commonSelector(state);
    const subset = {} as Pick<typeof fullSelection, T>;
    
    for (const key of keys) {
      subset[key] = fullSelection[key];
    }
    
    return subset;
  };
};