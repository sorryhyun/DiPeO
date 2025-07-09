/**
 * Data access hooks for reading store data
 * These hooks provide read-only access to store state
 */

import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '../unifiedStore';
import type { NodeID, ArrowID, PersonID, HandleID } from '@/core/types';

// === Entity Data Hooks ===

/**
 * Get all diagram data (nodes and arrows)
 */
export const useDiagramData = () => useUnifiedStore(
  useShallow(state => ({
    nodes: state.nodesArray,
    arrows: state.arrowsArray,
    handles: Array.from(state.handles.values()),
  }))
);

/**
 * Get node data by ID
 */
export const useNodeData = (nodeId: NodeID | null) => 
  useUnifiedStore(state => nodeId ? state.nodes.get(nodeId) : null);

/**
 * Get all nodes as array
 */
export const useNodesData = () => 
  useUnifiedStore(state => state.nodesArray);

/**
 * Get arrow data by ID
 */
export const useArrowData = (arrowId: ArrowID | null) => 
  useUnifiedStore(state => arrowId ? state.arrows.get(arrowId) : null);

/**
 * Get all arrows as array
 */
export const useArrowsData = () => 
  useUnifiedStore(state => state.arrowsArray);

/**
 * Get person data by ID
 */
export const usePersonData = (personId: PersonID | null) => 
  useUnifiedStore(state => personId ? state.persons.get(personId) : null);

/**
 * Get all persons as array
 */
export const usePersonsData = () => 
  useUnifiedStore(state => state.personsArray);

/**
 * Get handle data by ID
 */
export const useHandleData = (handleId: HandleID | null) => 
  useUnifiedStore(state => handleId ? state.handles.get(handleId) : null);

/**
 * Get handles for a specific node
 */
export const useNodeHandlesData = (nodeId: NodeID | null) => 
  useUnifiedStore(state => {
    if (!nodeId) return [];
    const handles = state.handleIndex.get(nodeId) || [];
    return handles;
  });

// === Execution Data Hooks ===

/**
 * Get execution data
 */
export const useExecutionData = () => useUnifiedStore(
  useShallow(state => ({
    isRunning: state.execution.isRunning,
    executionId: state.execution.id,
    isPaused: state.execution.isPaused,
    nodeStates: state.execution.nodeStates,
    runningNodes: state.execution.runningNodes,
    context: state.execution.context,
  }))
);

/**
 * Get execution state for a specific node
 */
export const useNodeExecutionData = (nodeId: NodeID) =>
  useUnifiedStore(state => state.execution.nodeStates.get(nodeId));

// === Selection Data Hooks ===

/**
 * Get current selection data
 */
export const useSelectionData = () => useUnifiedStore(
  useShallow(state => ({
    selectedId: state.selectedId,
    selectedType: state.selectedType,
    multiSelectedIds: state.multiSelectedIds,
    highlightedPersonId: state.highlightedPersonId,
  }))
);

/**
 * Get the currently selected entity (node, arrow, or person)
 */
export const useSelectedEntityData = () =>
  useUnifiedStore(state => {
    if (!state.selectedId || !state.selectedType) return null;

    switch (state.selectedType) {
      case 'node':
        return state.nodes.get(state.selectedId as NodeID);
      case 'arrow':
        return state.arrows.get(state.selectedId as ArrowID);
      case 'person':
        return state.persons.get(state.selectedId as PersonID);
      default:
        return null;
    }
  });

// === UI Data Hooks ===

/**
 * Get UI state data
 */
export const useUIData = () => useUnifiedStore(
  useShallow(state => ({
    readOnly: state.readOnly,
    activeView: state.activeView,
    activeCanvas: state.activeCanvas,
    dashboardTab: state.dashboardTab,
    isMonitorMode: state.isMonitorMode,
    canvasMode: state.canvasMode,
  }))
);

// === History Data Hooks ===

/**
 * Get history state
 */
export const useHistoryData = () => useUnifiedStore(
  useShallow(state => ({
    canUndo: state.canUndo,
    canRedo: state.canRedo,
    undoStackSize: state.history.undoStack.length,
    redoStackSize: state.history.redoStack.length,
    isInTransaction: state.history.currentTransaction !== null,
  }))
);