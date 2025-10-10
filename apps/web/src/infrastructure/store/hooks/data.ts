// Data access hooks for reading store data

import { useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '../unifiedStore';
import type { NodeID, ArrowID, PersonID, HandleID } from '@/infrastructure/types';

// === Entity Data Hooks ===

/**
 * Get all diagram data (nodes and arrows)
 */
export const useDiagramData = () => useUnifiedStore(
  useShallow(state => ({
    nodes: state.nodesArray,
    arrows: state.arrowsArray,
    handles: state.handlesArray,
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
 * Note: We need to track both the Map reference AND the value at the key
 * to ensure re-renders when node state changes
 */
export const useNodeExecutionData = (nodeId: NodeID) =>
  useUnifiedStore(state => {
    // Force re-render by accessing both the Map and the specific value
    const map = state.execution.nodeStates;
    return map.get(nodeId);
  });

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

// === Computed Execution Data Hooks ===

/**
 * Get running nodes from computed store
 */
export const useRunningNodesComputed = () => {
  const nodes = useUnifiedStore(state => state.nodesArray);
  const runningNodeIds = useUnifiedStore(state => state.execution.runningNodes);

  return useMemo(() =>
    nodes.filter(node => runningNodeIds.has(node.id)),
    [nodes, runningNodeIds]
  );
};

/**
 * Get completed nodes from computed store
 */
export const useCompletedNodesComputed = () => {
  const nodes = useUnifiedStore(state => state.nodesArray);
  const nodeStates = useUnifiedStore(state => state.execution.nodeStates);

  return useMemo(() =>
    nodes.filter(node => {
      const nodeState = nodeStates.get(node.id);
      return nodeState?.status === 'completed';
    }),
    [nodes, nodeStates]
  );
};

/**
 * Get failed nodes from computed store
 */
export const useFailedNodesComputed = () => {
  const nodes = useUnifiedStore(state => state.nodesArray);
  const nodeStates = useUnifiedStore(state => state.execution.nodeStates);

  return useMemo(() =>
    nodes.filter(node => {
      const nodeState = nodeStates.get(node.id);
      return nodeState?.status === 'failed';
    }),
    [nodes, nodeStates]
  );
};

/**
 * Get execution progress from computed store
 */
export const useExecutionProgressComputed = () => {
  const totalNodes = useUnifiedStore(state => state.nodes.size);
  const nodeStates = useUnifiedStore(state => state.execution.nodeStates);

  return useMemo(() => {
    const completed = Array.from(nodeStates.values())
      .filter(nodeState =>
        nodeState.status === 'completed' ||
        nodeState.status === 'skipped' ||
        nodeState.status === 'failed'
      ).length;

    return {
      completed,
      total: totalNodes,
      percentage: totalNodes > 0 ? Math.round((completed / totalNodes) * 100) : 0
    };
  }, [totalNodes, nodeStates]);
};
