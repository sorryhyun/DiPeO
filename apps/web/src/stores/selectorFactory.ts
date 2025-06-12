import type { UnifiedStore } from './unifiedStore.types';

/**
 * Common store selector factory to eliminate duplication across hooks
 * This reduces ~120 lines and ensures all hooks stay in sync
 */

export const createCommonStoreSelector = () => (state: UnifiedStore) => ({
  // === Raw data from store ===
  nodes: state.nodes,
  nodesMap: state.nodes, // Alias for compatibility
  handles: state.handles,
  handlesMap: state.handles, // Alias for compatibility
  arrows: state.arrows,
  persons: state.persons,
  apiKeys: state.apiKeys,
  
  // === Version tracking ===
  dataVersion: state.dataVersion,
  
  // === Mode flags ===
  isMonitorMode: state.readOnly,
  isExecutionMode: state.executionReadOnly,
  
  // === Selection state ===
  selectedId: state.selectedId,
  selectedType: state.selectedType,
  
  // === Execution state ===
  executionId: state.execution.id,
  isRunning: state.execution.isRunning,
  runningNodes: state.execution.runningNodes,
  nodeStates: state.execution.nodeStates,
  context: state.execution.context,
  
  // === History state ===
  canUndo: state.history.undoStack.length > 0,
  canRedo: state.history.redoStack.length > 0,
  
  // === Store actions (stable references) ===
  // Node operations
  addNode: state.addNode,
  updateNode: state.updateNode,
  deleteNode: state.deleteNode,
  updateNodeSilently: state.updateNodeSilently,

  // Arrow operations
  addArrow: state.addArrow,
  updateArrow: state.updateArrow,
  deleteArrow: state.deleteArrow,
  
  // Person operations
  addPerson: state.addPerson,
  updatePerson: state.updatePerson,
  deletePerson: state.deletePerson,
  
  // API Key operations
  addApiKey: state.addApiKey,
  updateApiKey: state.updateApiKey,
  deleteApiKey: state.deleteApiKey,
  
  // Selection operations
  select: state.select,
  clearSelection: state.clearSelection,
  
  // Execution operations
  startExecution: state.startExecution,
  updateNodeExecution: state.updateNodeExecution,
  stopExecution: state.stopExecution,
  
  // History operations
  transaction: state.transaction,
  undo: state.undo,
  redo: state.redo,
});

/**
 * Create a subset selector for specific use cases
 */
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