import { shallow } from 'zustand/shallow';
import { useUnifiedStore } from '@/stores/useUnifiedStore';
import type { DomainNode, DomainArrow, DomainPerson, DomainHandle, DomainApiKey, DomainDiagram, LLMService } from '@/types/domain';
import type { NodeID, ArrowID, PersonID, ApiKeyID, HandleID } from '@/types/branded';
import { nodeToReact } from '@/types/framework/adapters';
import type { NodeChange, EdgeChange, Connection } from '@xyflow/react';
import type { NodeKind, Vec2 } from '@/types/primitives';

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

// Canvas state - combines multiple related selectors with monitor support
export const useCanvasState = () => {
  return useUnifiedStore(
    state => {
      // Convert domain nodes to React Flow format with handles
      const domainNodes = Array.from(state.nodes.values());
      const nodes = domainNodes.map(node => {
        const nodeHandles = Array.from(state.handles.values()).filter(h => h.nodeId === node.id);
        return nodeToReact(node, nodeHandles);
      });
      
      return {
        nodes,
        arrows: Array.from(state.arrows.values()),
        isMonitorMode: state.readOnly,
        onNodesChange: (changes: NodeChange[]) => {
          // Handle node changes (position updates, etc.)
          changes.forEach((change) => {
            if (change.type === 'position' && change.position) {
              state.updateNode(change.id as NodeID, { position: change.position });
            }
          });
        },
        onArrowsChange: (changes: EdgeChange[]) => {
          // Handle arrow changes
          changes.forEach((change) => {
            if (change.type === 'remove') {
              state.deleteArrow(change.id as ArrowID);
            }
          });
        },
        onConnect: (connection: Connection) => {
          if (connection.source && connection.target && connection.sourceHandle && connection.targetHandle) {
            state.addArrow(
              connection.sourceHandle as HandleID,
              connection.targetHandle as HandleID
            );
          }
        },
        addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
          state.addNode(type as NodeKind, position, data),
        deleteNode: state.deleteNode,
        deleteArrow: state.deleteArrow,
      };
    },
    shallow
  );
};

// Person operations with monitor support
export const usePersons = () => {
  return useUnifiedStore(
    state => ({
      persons: Array.from(state.persons.values()),
      isMonitorMode: state.readOnly,
      addPerson: (person: { name: string; service: string; model: string }) => 
        state.addPerson(person.name, person.service as LLMService, person.model),
      updatePerson: state.updatePerson,
      deletePerson: state.deletePerson,
      getPersonById: (id: PersonID) => state.persons.get(id),
    }),
    shallow
  );
};

// Node operations with monitor support
export const useNodes = () => {
  return useUnifiedStore(
    state => {
      // Convert domain nodes to React Flow format with handles
      const domainNodes = Array.from(state.nodes.values());
      const nodes = domainNodes.map(node => {
        const nodeHandles = Array.from(state.handles.values()).filter(h => h.nodeId === node.id);
        return nodeToReact(node, nodeHandles);
      });
      
      return {
        nodes,
        isMonitorMode: state.readOnly,
        onNodesChange: (changes: NodeChange[]) => {
          changes.forEach((change) => {
            if (change.type === 'position' && change.position) {
              state.updateNode(change.id as NodeID, { position: change.position });
            }
          });
        },
        addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
          state.addNode(type as NodeKind, position, data),
        deleteNode: state.deleteNode,
      };
    },
    shallow
  );
};

// Arrow operations with monitor support
export const useArrows = () => {
  return useUnifiedStore(
    state => ({
      arrows: Array.from(state.arrows.values()),
      isMonitorMode: state.readOnly,
      onArrowsChange: (changes: EdgeChange[]) => {
        changes.forEach((change) => {
          if (change.type === 'remove') {
            state.deleteArrow(change.id as ArrowID);
          }
        });
      },
      onConnect: (connection: Connection) => {
        if (connection.source && connection.target && connection.sourceHandle && connection.targetHandle) {
          state.addArrow(
            connection.sourceHandle as HandleID,
            connection.targetHandle as HandleID
          );
        }
      },
      deleteArrow: state.deleteArrow,
    }),
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
    setActiveView: (view: 'diagram' | 'execution') => {
      // Update activeView in the store directly
      useUnifiedStore.setState((state) => ({ ...state, activeView: view }));
    },
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

// Grouped selectors for major components
export const useCanvasSelectors = () => {
  return useUnifiedStore(
    state => {
      // Convert domain nodes to React Flow format with handles
      const domainNodes = Array.from(state.nodes.values());
      const nodes = domainNodes.map(node => {
        const nodeHandles = Array.from(state.handles.values()).filter(h => h.nodeId === node.id);
        return nodeToReact(node, nodeHandles);
      });
      
      return {
        nodes,
        arrows: Array.from(state.arrows.values()),
        isMonitorMode: state.readOnly,
        onNodesChange: (changes: NodeChange[]) => {
          changes.forEach((change) => {
            if (change.type === 'position' && change.position) {
              state.updateNode(change.id as NodeID, { position: change.position });
            }
          });
        },
        onArrowsChange: (changes: EdgeChange[]) => {
          changes.forEach((change) => {
            if (change.type === 'remove') {
              state.deleteArrow(change.id as ArrowID);
            }
          });
        },
        onConnect: (connection: Connection) => {
          if (connection.source && connection.target && connection.sourceHandle && connection.targetHandle) {
            state.addArrow(
              connection.sourceHandle as HandleID,
              connection.targetHandle as HandleID
            );
          }
        },
        addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
          state.addNode(type as NodeKind, position, data),
        deleteNode: state.deleteNode,
        deleteArrow: state.deleteArrow,
        updateNode: state.updateNode,
      };
    },
    shallow
  );
};

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

// Node data updater hook
export const useNodeDataUpdater = () => {
  return useUnifiedStore(state => state.updateNode);
};

// Arrow data updater hook
export const useArrowDataUpdater = () => {
  return useUnifiedStore(state => state.updateArrow);
};

// Person data updater hook
export const usePersonDataUpdater = () => {
  return useUnifiedStore(state => state.updatePerson);
};

// API key updater hook
export const useApiKeyUpdater = () => {
  const apiKeys = useUnifiedStore(state => state.apiKeys);
  const transaction = useUnifiedStore(state => state.transaction);
  
  return (id: ApiKeyID, updates: Partial<DomainApiKey>) => {
    transaction(() => {
      const key = apiKeys.get(id);
      if (key) {
        Object.assign(key, updates);
      }
    });
  };
};

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
      setNodeError: (nodeId: NodeID, error: string) => {
        state.updateNodeExecution(nodeId, { 
          status: 'failed', 
          error,
          timestamp: Date.now()
        });
      },
    }),
    shallow
  );
};

// Node position updater
export const useNodePositionUpdater = () => {
  return useUnifiedStore(state => (id: NodeID, position: { x: number; y: number }) => 
    state.updateNode(id, { position })
  );
};

// Selected element getters
export const useSelectedNodeId = () => {
  return useUnifiedStore(state => 
    state.selectedType === 'node' ? state.selectedId as NodeID : null
  );
};

export const useSelectedArrowId = () => {
  return useUnifiedStore(state => 
    state.selectedType === 'arrow' ? state.selectedId as ArrowID : null
  );
};

// Batch selectors for common operations
export const useDiagramActions = () => {
  return useUnifiedStore(
    state => ({
      addNode: (node: DomainNode) => state.addNode(node.type, node.position, node.data),
      addNodeByType: (type: NodeKind, position: Vec2, data?: Record<string, unknown>) => 
        state.addNode(type, position, data),
      deleteNode: state.deleteNode,
      addArrow: (arrow: DomainArrow) => state.addArrow(arrow.source, arrow.target, arrow.data),
      deleteArrow: state.deleteArrow,
      clearDiagram: () => {
        state.transaction(() => {
          state.nodes.clear();
          state.arrows.clear();
          state.handles.clear();
          state.persons.clear();
          state.apiKeys.clear();
          state.clearSelection();
        });
      },
    }),
    shallow
  );
};

// History operations
export const useHistorySelectors = () => {
  return useUnifiedStore(
    state => ({
      undo: state.undo,
      redo: state.redo,
      canUndo: state.history.undoStack.length > 0,
      canRedo: state.history.redoStack.length > 0,
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
export const useIsReadOnly = () => useUnifiedStore(state => state.readOnly);
export const useApiKeys = () => useUnifiedStore(state => Array.from(state.apiKeys.values()));