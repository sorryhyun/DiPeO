import { shallow } from 'zustand/shallow';
import { useDiagramStore } from '@/stores';
import { useExecutionStore } from '@/stores/executionStore';
import { useConsolidatedUIStore } from '@/stores/consolidatedUIStore';
import type { Node, Arrow, Person, ApiKey } from '@/types';

// ===== Key Optimized Selectors =====

// Execution state for specific node - avoids subscribing to entire execution store
export const useNodeExecutionState = (nodeId: string) => {
  return useExecutionStore(
    state => {
      const isRunning = state.runningNodes.includes(nodeId);
      const isCurrentRunning = state.currentRunningNode === nodeId;
      const nodeRunningState = state.nodeRunningStates[nodeId] || false;
      const skippedNodeInfo = state.skippedNodes[nodeId];
      const isSkipped = Boolean(skippedNodeInfo);
      
      // Debug logging for node execution state
      if (isRunning || nodeRunningState || isSkipped) {
        console.log(`[useNodeExecutionState] Node ${nodeId} state:`, {
          nodeId,
          isRunning,
          isCurrentRunning,
          nodeRunningState,
          isSkipped,
          skipReason: skippedNodeInfo?.reason,
          runningNodes: state.runningNodes,
          lastUpdate: state.lastUpdate
        });
      }
      
      return {
        isRunning,
        isCurrentRunning,
        nodeRunningState,
        isSkipped,
        skipReason: skippedNodeInfo?.reason,
      };
    },
    shallow
  );
};

// Canvas state - combines multiple related selectors with monitor support
export const useCanvasState = () => {
  return useDiagramStore(
    state => ({
      nodes: state.nodeList(),
      arrows: state.arrowList(),
      isMonitorMode: state.isReadOnly,
      onNodesChange: state.onNodesChange,
      onArrowsChange: state.onArrowsChange,
      onConnect: state.onConnect,
      addNode: state.addNode,
      deleteNode: state.deleteNode,
      deleteArrow: state.deleteArrow,
    }),
    shallow
  );
};

// Person operations with monitor support
export const usePersons = () => {
  return useDiagramStore(
    state => ({
      persons: state.personList(),
      isMonitorMode: state.isReadOnly,
      addPerson: state.addPerson,
      updatePerson: state.updatePerson,
      deletePerson: state.deletePerson,
      getPersonById: state.getPersonById,
    }),
    shallow
  );
};

// Node operations with monitor support
export const useNodes = () => {
  return useDiagramStore(
    state => ({
      nodes: state.nodeList(),
      isMonitorMode: state.isReadOnly,
      onNodesChange: state.onNodesChange,
      addNode: state.addNode,
      deleteNode: state.deleteNode,
    }),
    shallow
  );
};

// Arrow operations with monitor support
export const useArrows = () => {
  return useDiagramStore(
    state => ({
      arrows: state.arrowList(),
      isMonitorMode: state.isReadOnly,
      onArrowsChange: state.onArrowsChange,
      onConnect: state.onConnect,
      deleteArrow: state.deleteArrow,
    }),
    shallow
  );
};

// UI state selectors
export const useSelectedElement = () => {
  return useConsolidatedUIStore(
    state => ({
      selectedNodeId: state.selectedNodeId,
      selectedArrowId: state.selectedArrowId,
      selectedPersonId: state.selectedPersonId,
      setSelectedNodeId: state.setSelectedNodeId,
      setSelectedArrowId: state.setSelectedArrowId,
      setSelectedPersonId: state.setSelectedPersonId,
      clearSelection: state.clearSelection,
    }),
    shallow
  );
};

export const useUIState = () => {
  return useConsolidatedUIStore(
    state => ({
      dashboardTab: state.dashboardTab,
      setDashboardTab: state.setDashboardTab,
      activeCanvas: state.activeCanvas,
      setActiveCanvas: state.setActiveCanvas,
      toggleCanvas: state.toggleCanvas,
      activeView: state.activeView,
      setActiveView: state.setActiveView,
      showApiKeysModal: state.showApiKeysModal,
      showExecutionModal: state.showExecutionModal,
      openApiKeysModal: state.openApiKeysModal,
      closeApiKeysModal: state.closeApiKeysModal,
      openExecutionModal: state.openExecutionModal,
      closeExecutionModal: state.closeExecutionModal,
      hasSelection: state.hasSelection,
    }),
    shallow
  );
};

// Execution status
export const useExecutionStatus = () => {
  return useExecutionStore(
    state => ({
      runContext: state.runContext,
      runningNodes: state.runningNodes,
      currentRunningNode: state.currentRunningNode,
      nodeRunningStates: state.nodeRunningStates,
    }),
    shallow
  );
};


// Utility functions that add logic

// Grouped selectors for major components
export const useCanvasSelectors = () => {
  return useDiagramStore(
    state => ({
      nodes: state.nodeList(),
      arrows: state.arrowList(),
      isMonitorMode: state.isReadOnly,
      onNodesChange: state.onNodesChange,
      onArrowsChange: state.onArrowsChange,
      onConnect: state.onConnect,
      addNode: state.addNode,
      deleteNode: state.deleteNode,
      deleteArrow: state.deleteArrow,
      updateNode: state.updateNode,
    }),
    shallow
  );
};

export const useExecutionSelectors = () => {
  return useExecutionStore(
    state => ({
      runContext: state.runContext,
      runningNodes: state.runningNodes,
      currentRunningNode: state.currentRunningNode,
      nodeRunningStates: state.nodeRunningStates,
      skippedNodes: state.skippedNodes,
    }),
    shallow
  );
};

// ===== Missing exports that were removed =====

// Node data updater hook
export const useNodeDataUpdater = () => {
  return useDiagramStore(state => state.updateNode);
};

// Arrow data updater hook
export const useArrowDataUpdater = () => {
  return useDiagramStore(state => state.updateArrow);
};

// UI selectors (alias for backward compatibility)
// export const useUISelectors = useUIState; // Removed - use useUIState directly

// History selectors (if needed, can be extended later)
export const useHistorySelectors = () => {
  // Placeholder for history functionality
  return {
    canUndo: false,
    canRedo: false,
    undo: () => {},
    redo: () => {},
  };
};

// Diagram operations as direct exports
export const exportDiagramState = () => {
  return useDiagramStore.getState().exportDiagram();
};

interface DiagramData {
  nodes?: Node[];
  arrows?: Arrow[];
  persons?: Person[];
  apiKeys?: ApiKey[];
}

export const loadDiagram = (data: DiagramData) => {
  // Ensure required fields have default values
  const diagramData = {
    nodes: data.nodes || [],
    arrows: data.arrows || [],
    persons: data.persons || [],
    apiKeys: data.apiKeys
  };
  return useDiagramStore.getState().loadDiagram(diagramData);
};

export const clearDiagram = () => {
  return useDiagramStore.getState().clear();
};


