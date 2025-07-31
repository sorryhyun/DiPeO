// Operation hooks for store mutations and actions

import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '../unifiedStore';

// === Diagram Operations ===

/**
 * Get diagram mutation operations
 */
export const useDiagramOperations = () => useUnifiedStore(
  useShallow(state => ({
    // Node operations
    addNode: state.addNode,
    updateNode: state.updateNode,
    deleteNode: state.deleteNode,
    batchUpdateNodes: state.batchUpdateNodes,
    batchDeleteNodes: state.batchDeleteNodes,
    
    // Arrow operations
    addArrow: state.addArrow,
    updateArrow: state.updateArrow,
    deleteArrow: state.deleteArrow,
    
    // Diagram operations
    clearDiagram: state.clearDiagram,
    restoreDiagram: state.restoreDiagram,
    setDiagramId: state.setDiagramId,
    setDiagramName: state.setDiagramName,
    setDiagramDescription: state.setDiagramDescription,
  }))
);

/**
 * Get node-specific operations
 */
export const useNodeOperations = () => useUnifiedStore(
  useShallow(state => ({
    addNode: state.addNode,
    updateNode: state.updateNode,
    deleteNode: state.deleteNode,
    batchUpdateNodes: state.batchUpdateNodes,
    batchDeleteNodes: state.batchDeleteNodes,
  }))
);

/**
 * Get arrow-specific operations
 */
export const useArrowOperations = () => useUnifiedStore(
  useShallow(state => ({
    addArrow: state.addArrow,
    updateArrow: state.updateArrow,
    deleteArrow: state.deleteArrow,
  }))
);

// === Person Operations ===

/**
 * Get person management operations
 */
export const usePersonOperations = () => useUnifiedStore(
  useShallow(state => ({
    addPerson: state.addPerson,
    updatePerson: state.updatePerson,
    deletePerson: state.deletePerson,
    clearPersons: state.clearPersons,
    restorePersons: state.restorePersons,
  }))
);

// === Execution Operations ===

/**
 * Get execution control operations
 */
export const useExecutionOperations = () => useUnifiedStore(
  useShallow(state => ({
    startExecution: state.startExecution,
    stopExecution: state.stopExecution,
    pauseExecution: state.pauseExecution,
    resumeExecution: state.resumeExecution,
    updateNodeExecution: state.updateNodeExecution,
    setNodeRunning: state.setNodeRunning,
    setNodeCompleted: state.setNodeCompleted,
    setNodeFailed: state.setNodeFailed,
    setNodeSkipped: state.setNodeSkipped,
    updateExecutionContext: state.updateExecutionContext,
    clearExecutionContext: state.clearExecutionContext,
  }))
);

// === Selection Operations ===

/**
 * Get selection operations
 */
export const useSelectionOperations = () => useUnifiedStore(
  useShallow(state => ({
    select: state.select,
    multiSelect: state.multiSelect,
    toggleSelection: state.toggleSelection,
    clearSelection: state.clearSelection,
    selectAll: state.selectAll,
    highlightPerson: state.highlightPerson,
  }))
);

// === UI Operations ===

/**
 * Get UI control operations
 */
export const useUIOperations = () => useUnifiedStore(
  useShallow(state => ({
    setReadOnly: state.setReadOnly,
    setActiveView: state.setActiveView,
    setActiveCanvas: state.setActiveCanvas,
    setDashboardTab: state.setDashboardTab,
    setViewport: state.setViewport,
    setZoom: state.setZoom,
    setPosition: state.setPosition,
    setCanvasMode: state.setCanvasMode,
    setMonitorMode: state.setMonitorMode,
    clearUIState: state.clearUIState,
  }))
);

// === History Operations ===

/**
 * Get history operations
 */
export const useHistoryOperations = () => useUnifiedStore(
  useShallow(state => ({
    undo: state.undo,
    redo: state.redo,
    transaction: state.transaction,
  }))
);

// === Global Operations ===

/**
 * Get global store operations
 */
export const useGlobalOperations = () => useUnifiedStore(
  useShallow(state => ({
    clearAll: state.clearAll,
    transaction: state.transaction,
  }))
);