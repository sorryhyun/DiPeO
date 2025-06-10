import { shallow } from 'zustand/shallow';
import { useUnifiedStore } from '@/stores/useUnifiedStore';
import type { DomainNode, DomainArrow, DomainPerson, DomainHandle, DomainApiKey, DomainDiagram } from '@/types/domain';
import type { NodeID, ArrowID, PersonID, ApiKeyID, HandleID } from '@/types/branded';

// ===== Key Optimized Selectors =====

// Execution state for specific node - avoids subscribing to entire execution store
export const useNodeExecutionState = (nodeId: NodeID) => {
  return useUnifiedStore(
    state => {
      const isRunning = state.execution.runningNodes.has(nodeId);
      const nodeState = state.execution.nodeStates.get(nodeId);
      const isSkipped = nodeState?.status === 'skipped';
      
      // Debug logging for node execution state
      if (isRunning || isSkipped) {
        console.log(`[useNodeExecutionState] Node ${nodeId} state:`, {
          nodeId,
          isRunning,
          nodeState,
          isSkipped,
          runningNodes: Array.from(state.execution.runningNodes),
        });
      }
      
      return {
        isRunning,
        isCurrentRunning: isRunning, // In unified store, running means current
        nodeRunningState: isRunning,
        isSkipped,
        skipReason: nodeState?.error,
      };
    },
    shallow
  );
};



// UI state selectors
export const useSelectedElement = () => {
  return useUnifiedStore(
    state => ({
      selectedNodeId: state.selectedType === 'node' ? state.selectedId as NodeID : null,
      selectedArrowId: state.selectedType === 'arrow' ? state.selectedId as ArrowID : null,
      selectedPersonId: state.selectedType === 'person' ? state.selectedId as PersonID : null,
      setSelectedNodeId: (id: NodeID | null) => {
        if (id) state.select(id, 'node');
        else state.clearSelection();
      },
      setSelectedArrowId: (id: ArrowID | null) => {
        if (id) state.select(id, 'arrow');
        else state.clearSelection();
      },
      setSelectedPersonId: (id: PersonID | null) => {
        if (id) state.select(id, 'person');
        else state.clearSelection();
      },
      clearSelection: state.clearSelection,
    }),
    shallow
  );
};

export const useUIState = () => {
  const store = useUnifiedStore();
  
  return {
    dashboardTab: store.dashboardTab,
    setDashboardTab: store.setDashboardTab,
    activeCanvas: store.activeCanvas as 'main' | 'execution' | 'memory',
    setActiveCanvas: store.setActiveCanvas,
    toggleCanvas: () => {
      const canvases: ('main' | 'execution' | 'memory')[] = ['main', 'execution', 'memory'];
      const currentCanvas = store.activeCanvas || 'main';
      const currentIndex = canvases.indexOf(currentCanvas);
      const nextIndex = (currentIndex + 1) % canvases.length;
      store.setActiveCanvas(canvases[nextIndex] as 'main' | 'execution' | 'memory');
    },
    activeView: store.activeView,
    showApiKeysModal: store.showApiKeysModal,
    showExecutionModal: store.showExecutionModal,
    openApiKeysModal: store.openApiKeysModal,
    closeApiKeysModal: store.closeApiKeysModal,
    openExecutionModal: store.openExecutionModal,
    closeExecutionModal: store.closeExecutionModal,
    hasSelection: store.selectedId !== null,
  };
};

// Execution status
export const useExecutionStatus = () => {
  return useUnifiedStore(
    state => ({
      runContext: state.execution.context,
      runningNodes: Array.from(state.execution.runningNodes),
      currentRunningNode: Array.from(state.execution.runningNodes)[0] || null,
      nodeRunningStates: Object.fromEntries(
        Array.from(state.execution.nodeStates.entries()).map(([id, state]) => [id, state.status === 'running'])
      ),
    }),
    shallow
  );
};

// Utility functions that add logic


export const useExecutionSelectors = () => {
  return useUnifiedStore(
    state => ({
      runContext: state.execution.context,
      runningNodes: Array.from(state.execution.runningNodes),
      currentRunningNode: Array.from(state.execution.runningNodes)[0] || null,
      nodeRunningStates: Object.fromEntries(
        Array.from(state.execution.nodeStates.entries()).map(([id, state]) => [id, state.status === 'running'])
      ),
      skippedNodes: Object.fromEntries(
        Array.from(state.execution.nodeStates.entries())
          .filter(([_, state]) => state.status === 'skipped')
          .map(([id, state]) => [id, { reason: state.error || 'Skipped' }])
      ),
    }),
    shallow
  );
};

// ===== Missing exports that were removed =====





// Granular execution actions selector
export const useExecutionActions = () => {
  return useUnifiedStore(
    state => ({
      startExecution: state.startExecution,
      stopExecution: state.stopExecution,
      reset: () => {
        state.stopExecution();
        state.execution.nodeStates.clear();
        state.execution.context = {};
      },
      addRunningNode: (nodeId: NodeID) => {
        state.execution.runningNodes.add(nodeId);
      },
      removeRunningNode: (nodeId: NodeID) => {
        state.execution.runningNodes.delete(nodeId);
      },
      setCurrentRunningNode: (nodeId: NodeID | null) => {
        // In unified store, running nodes are tracked in a Set
        if (nodeId) {
          state.execution.runningNodes.clear();
          state.execution.runningNodes.add(nodeId);
        }
      },
      setRunContext: (context: Record<string, unknown>) => {
        state.execution.context = context;
      },
      addSkippedNode: (nodeId: NodeID, reason: string) => {
        state.updateNodeExecution(nodeId, { 
          status: 'skipped', 
          error: reason,
          timestamp: Date.now()
        });
      },
    }),
    shallow
  );
};





// Diagram export/import operations
export const exportDiagramState = (): DomainDiagram | null => {
  const state = useUnifiedStore.getState();
  
  if (state.nodes.size === 0) return null;
  
  // Convert Maps to Records
  const nodes: Record<NodeID, DomainNode> = {};
  const arrows: Record<ArrowID, DomainArrow> = {};
  const persons: Record<PersonID, DomainPerson> = {};
  const handles: Record<HandleID, DomainHandle> = {};
  const apiKeys: Record<ApiKeyID, DomainApiKey> = {};
  
  state.nodes.forEach((node, id) => { nodes[id] = node; });
  state.arrows.forEach((arrow, id) => { arrows[id] = arrow; });
  state.persons.forEach((person, id) => { persons[id] = person; });
  state.handles.forEach((handle, id) => { handles[id] = handle; });
  state.apiKeys.forEach((key, id) => { apiKeys[id] = key; });
  
  return {
    nodes,
    arrows,
    persons,
    handles,
    apiKeys,
  };
};

export const loadDiagram = (diagram: DomainDiagram) => {
  const state = useUnifiedStore.getState();
  
  state.transaction(() => {
    // Clear existing data
    state.nodes.clear();
    state.arrows.clear();
    state.handles.clear();
    state.persons.clear();
    state.apiKeys.clear();
    
    // Load new data from Records
    Object.entries(diagram.nodes).forEach(([id, node]) => state.nodes.set(id as NodeID, node));
    Object.entries(diagram.arrows).forEach(([id, arrow]) => state.arrows.set(id as ArrowID, arrow));
    Object.entries(diagram.handles).forEach(([id, handle]) => state.handles.set(id as HandleID, handle));
    Object.entries(diagram.persons).forEach(([id, person]) => state.persons.set(id as PersonID, person));
    if (diagram.apiKeys) {
      Object.entries(diagram.apiKeys).forEach(([id, key]) => state.apiKeys.set(id as ApiKeyID, key));
    }
  });
};

export const clearDiagram = () => {
  const state = useUnifiedStore.getState();
  
  state.transaction(() => {
    state.nodes.clear();
    state.arrows.clear();
    state.handles.clear();
    state.persons.clear();
    state.apiKeys.clear();
    state.clearSelection();
  });
};

// For read-only state access (useful for components that just need to read state)
export const useApiKeys = () => useUnifiedStore(state => Array.from(state.apiKeys.values()));

// Re-export these for backward compatibility until all components are updated
export const usePersons = () => {
  return useUnifiedStore(
    state => ({
      persons: Array.from(state.persons.values()),
      isMonitorMode: state.readOnly,
      addPerson: (person: { name: string; service: string; model: string }) => 
        state.addPerson(person.name, person.service as any, person.model),
      updatePerson: state.updatePerson,
      deletePerson: state.deletePerson,
      getPersonById: (id: PersonID) => state.persons.get(id),
    }),
    shallow
  );
};

export const useNodeDataUpdater = () => {
  return useUnifiedStore(state => state.updateNode);
};

export const useArrowDataUpdater = () => {
  return useUnifiedStore(state => state.updateArrow);
};