import { shallow } from 'zustand/shallow';
import { useDiagramStore } from '@/stores';
import { useExecutionStore } from '@/stores/executionStore';
import { useConsolidatedUIStore } from '@/stores/consolidatedUIStore';
import type { DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle, DomainDiagram } from '@/types/domain';
import type { NodeID, ArrowID, PersonID, ApiKeyID, HandleID } from '@/types/branded';

// ===== Key Optimized Selectors =====

// Execution state for specific node - avoids subscribing to entire execution store
export const useNodeExecutionState = (nodeId: NodeID) => {
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
      addNode: state.addNodeByType,
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
      addPerson: state.createPerson,
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
      addNode: state.addNodeByType,
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
      addNode: state.addNodeByType,
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

// Person data updater hook
export const usePersonDataUpdater = () => {
  return useDiagramStore(state => state.updatePerson);
};

// API key updater hook
export const useApiKeyUpdater = () => {
  return useDiagramStore(state => state.updateApiKey);
};

// Granular execution actions selector
export const useExecutionActions = () => {
  return useExecutionStore(
    state => ({
      startExecution: state.startExecution,
      stopExecution: state.stopExecution,
      reset: state.reset,
      addRunningNode: state.addRunningNode,
      removeRunningNode: state.removeRunningNode,
      setCurrentRunningNode: state.setCurrentRunningNode,
      setRunContext: state.setRunContext,
      addSkippedNode: state.addSkippedNode,
      setNodeError: state.setNodeError,
    }),
    shallow
  );
};

// Node position updater
export const useNodePositionUpdater = () => {
  return useDiagramStore(state => (id: NodeID, position: { x: number; y: number }) => 
    state.updateNode(id, { position })
  );
};

// Selected element getters
export const useSelectedNodeId = () => {
  return useConsolidatedUIStore(state => state.selectedNodeId);
};

export const useSelectedArrowId = () => {
  return useConsolidatedUIStore(state => state.selectedArrowId);
};

// Batch selectors for common operations
export const useDiagramActions = () => {
  return useDiagramStore(
    state => ({
      addNode: state.addNode,
      addNodeByType: state.addNodeByType,
      deleteNode: state.deleteNode,
      addArrow: state.addArrow,
      deleteArrow: state.deleteArrow,
      addPerson: state.addPerson,
      deletePerson: state.deletePerson,
      addApiKey: state.addApiKey,
      deleteApiKey: state.deleteApiKey,
    }),
    shallow
  );
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

export const loadDiagram = (data: any) => {
  // Convert old array format to new Record format if needed
  let diagramData: DomainDiagram;
  
  if (Array.isArray(data.nodes)) {
    // Old format with arrays - convert to Records
    const nodes: Record<NodeID, DomainNode> = {};
    const handles: Record<HandleID, DomainHandle> = {};
    const arrows: Record<ArrowID, DomainArrow> = {};
    const persons: Record<PersonID, DomainPerson> = {};
    const apiKeys: Record<ApiKeyID, DomainApiKey> = {};
    
    (data.nodes || []).forEach((node: DomainNode) => {
      nodes[node.id] = node;
    });
    
    (data.arrows || []).forEach((arrow: DomainArrow) => {
      arrows[arrow.id] = arrow;
    });
    
    (data.persons || []).forEach((person: DomainPerson) => {
      persons[person.id] = person;
    });
    
    (data.apiKeys || []).forEach((apiKey: DomainApiKey) => {
      apiKeys[apiKey.id] = apiKey;
    });
    
    diagramData = {
      nodes,
      handles,
      arrows,
      persons,
      apiKeys
    };
  } else {
    // New format with Records
    diagramData = data as DomainDiagram;
  }
  
  return useDiagramStore.getState().loadDiagram(diagramData);
};

export const clearDiagram = () => {
  return useDiagramStore.getState().clear();
};


