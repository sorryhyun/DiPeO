/**
 * CanvasContext (Refactored) - Simplified context with only 3 hooks
 * Provides shared state and operations for canvas components
 */

import React, { createContext, useContext, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useCanvas as useCanvasBase, useCanvasInteractions } from '@/features/diagram-editor/hooks';
import { useNodeOperations, useArrowOperations, usePersonOperations, useDiagramData, usePersonsData, useExecutionProgressComputed, useRunningNodesComputed, useCompletedNodesComputed, useFailedNodesComputed } from '@/core/store/hooks';
import { useExecution } from '@/features/execution-monitor/hooks';
import type { Vec2, ArrowID, NodeID, PersonID, DomainNode, DomainArrow, DomainPerson } from '@dipeo/domain-models';
import { nodeId, NodeType } from '@/core/types';

/**
 * Canvas state including UI, diagram data, and execution state
 */
export interface CanvasState {
  // Selection state
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  selectedNodeIds: Set<NodeID>;
  
  // Canvas UI state
  activeCanvas: 'main' | 'execution' | 'memory' | 'preview' | 'monitor';
  readOnly: boolean;
  isExecuting: boolean;
  isPaused: boolean;
  zoom: number;
  position: Vec2;
  canvasMode: 'select' | 'pan' | 'zoom';
  
  // Diagram data
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  personsWithUsage: Array<DomainPerson & { nodeCount: number }>;
  
  // Execution state
  nodeStates: Map<NodeID, any>;
  executionProgress: number;
  runningNodeCount: number;
  completedNodeCount: number;
  failedNodeCount: number;
  
  // Metadata
  diagramName: string;
  diagramId: string | null;
  dataVersion: number;
}

/**
 * Canvas operations including selection, CRUD, and canvas controls
 */
export interface CanvasOperations {
  // Selection operations
  selectNode: (nodeId: NodeID | null) => void;
  selectArrow: (arrowId: ArrowID | null) => void;
  selectPerson: (personId: PersonID | null) => void;
  selectMultipleNodes: (nodeIds: NodeID[]) => void;
  clearSelection: () => void;
  
  // Canvas controls
  setReadOnly: (readOnly: boolean) => void;
  setCanvasMode: (mode: 'select' | 'pan' | 'zoom') => void;
  
  // Diagram operations (unified)
  nodeOps: ReturnType<typeof useNodeOperations>;
  arrowOps: ReturnType<typeof useArrowOperations>;
  personOps: ReturnType<typeof usePersonOperations>;
  
  // Canvas and interaction handlers
  canvasHandlers: ReturnType<typeof useCanvasBase>;
  interactions: ReturnType<typeof useCanvasInteractions>;
  
  // Execution operations
  executionOps: ReturnType<typeof useExecution>;
  
  // Direct store operations
  clearDiagram: () => void;
  clearAll: () => void;
  validateDiagram: () => { isValid: boolean; errors: string[] };
}

/**
 * Complete canvas context value
 */
interface CanvasContextValue {
  state: CanvasState;
  operations: CanvasOperations;
}

const CanvasContext = createContext<CanvasContextValue | null>(null);

/**
 * CanvasProvider - Provides canvas context to children
 */
export function CanvasProvider({ children }: { children: React.ReactNode }) {
  // Get UI state from store
  const uiState = useUnifiedStore(
    useShallow(state => ({
      // Selection state
      selectedType: state.selectedType,
      selectedId: state.selectedId,
      multiSelectedIds: state.multiSelectedIds,
      
      // Canvas state
      activeCanvas: state.activeCanvas,
      readOnly: state.readOnly,
      isExecuting: state.execution.isRunning,
      isPaused: state.execution.isPaused,
      zoom: state.zoom,
      position: state.position,
      canvasMode: state.canvasMode,
      
      // Metadata
      diagramName: state.diagramName,
      diagramId: state.diagramId,
    }))
  );
  
  // Derive specific selection states
  const selectedNodeId = uiState.selectedType === 'node' ? (uiState.selectedId as NodeID) : null;
  const selectedArrowId = uiState.selectedType === 'arrow' ? (uiState.selectedId as ArrowID) : null;
  const selectedPersonId = uiState.selectedType === 'person' ? (uiState.selectedId as PersonID) : null;
  
  // Create selectedNodeIds Set
  const selectedNodeIds = useMemo(() => {
    const nodeIds = new Set<NodeID>();
    if (uiState.selectedType === 'node') {
      uiState.multiSelectedIds.forEach(id => {
        nodeIds.add(id as NodeID);
      });
    }
    return nodeIds;
  }, [uiState.multiSelectedIds, uiState.selectedType]);
  
  // Get store operations
  const storeOperations = useUnifiedStore(
    useShallow(state => ({
      select: state.select,
      clearSelection: state.clearSelection,
      multiSelect: state.multiSelect,
      setReadOnly: state.setReadOnly,
      setCanvasMode: state.setCanvasMode,
      clearDiagram: state.clearDiagram,
      clearAll: state.clearAll,
      validateDiagram: state.validateDiagram,
    }))
  );
  
  // Get data from hooks
  const diagramData = useDiagramData();
  const execution = useExecution({ showToasts: false });
  const personsArray = usePersonsData();
  
  // Memoize Map creations to prevent recreating on every render
  const nodesMap = useMemo(() => 
    new Map(diagramData.nodes.map((node: DomainNode) => [node.id, node])),
    [diagramData.nodes]
  );
  
  const arrowsMap = useMemo(() => 
    new Map(diagramData.arrows.map((arrow: DomainArrow) => [arrow.id, arrow])),
    [diagramData.arrows]
  );
  
  const personsMap = useMemo(() => 
    new Map(personsArray.map((person: DomainPerson) => [person.id, person])),
    [personsArray]
  );
  
  // Get computed execution data
  const executionProgress = useExecutionProgressComputed();
  const runningNodes = useRunningNodesComputed();
  const completedNodes = useCompletedNodesComputed();
  const failedNodes = useFailedNodesComputed();
  
  // Calculate persons with usage stats
  const personsWithUsage = useMemo(() => {
    const usageMap = new Map<PersonID, number>();
    
    // Count person usage in nodes
    nodesMap.forEach((node: any) => {
      const personId = node.data?.person || node.data?.personId;
      if (personId && (node.type === NodeType.PERSON_JOB || node.type === NodeType.PERSON_BATCH_JOB)) {
        usageMap.set(personId as PersonID, (usageMap.get(personId as PersonID) || 0) + 1);
      }
    });
    
    // Map persons with usage count
    return personsArray.map(person => ({
      ...person as DomainPerson,
      nodeCount: usageMap.get(person.id as PersonID) || 0
    }));
  }, [nodesMap, personsArray]);
  
  // Get operation hooks
  const canvasHandlers = useCanvasBase();
  const interactions = useCanvasInteractions();
  const nodeOps = useNodeOperations();
  const arrowOps = useArrowOperations();
  const personOps = usePersonOperations();
  const executionOps = useExecution();
  
  // Create selection operations
  const selectionOps = useMemo(() => ({
    selectNode: (nodeId: NodeID | null) => {
      if (nodeId) {
        storeOperations.select(nodeId, 'node');
      } else {
        storeOperations.clearSelection();
      }
    },
    selectArrow: (arrowId: ArrowID | null) => {
      if (arrowId) {
        storeOperations.select(arrowId, 'arrow');
      } else {
        storeOperations.clearSelection();
      }
    },
    selectPerson: (personId: PersonID | null) => {
      if (personId) {
        storeOperations.select(personId, 'person');
      } else {
        storeOperations.clearSelection();
      }
    },
    selectMultipleNodes: (nodeIds: NodeID[]) => {
      storeOperations.multiSelect(nodeIds, 'node');
    },
  }), [storeOperations]);
  
  // Build context value
  const contextValue = useMemo<CanvasContextValue>(() => ({
    state: {
      // Selection state
      selectedNodeId,
      selectedArrowId,
      selectedPersonId,
      selectedNodeIds,
      
      // Canvas UI state
      activeCanvas: uiState.activeCanvas,
      readOnly: uiState.readOnly,
      isExecuting: uiState.isExecuting,
      isPaused: uiState.isPaused,
      zoom: uiState.zoom,
      position: uiState.position,
      canvasMode: uiState.canvasMode,
      
      // Diagram data
      nodes: nodesMap,
      arrows: arrowsMap,
      persons: personsMap,
      personsWithUsage,
      
      // Execution state
      nodeStates: new Map(Object.entries(execution.nodeStates).map(([k, v]) => [nodeId(k), v])),
      executionProgress: executionProgress.percentage,
      runningNodeCount: runningNodes.length,
      completedNodeCount: completedNodes.length,
      failedNodeCount: failedNodes.length,
      
      // Metadata
      diagramName: uiState.diagramName,
      diagramId: uiState.diagramId,
      dataVersion: 0, // TODO: Add dataVersion to store hooks
    },
    operations: {
      // Selection operations
      ...selectionOps,
      clearSelection: storeOperations.clearSelection,
      
      // Canvas controls
      setReadOnly: storeOperations.setReadOnly,
      setCanvasMode: storeOperations.setCanvasMode,
      
      // Diagram operations
      nodeOps,
      arrowOps,
      personOps,
      
      // Canvas and interactions
      canvasHandlers,
      interactions,
      
      // Execution
      executionOps,
      
      // Direct store operations
      clearDiagram: storeOperations.clearDiagram,
      clearAll: storeOperations.clearAll,
      validateDiagram: storeOperations.validateDiagram,
    }
  }), [
    selectedNodeId, selectedArrowId, selectedPersonId, selectedNodeIds,
    uiState, nodesMap, arrowsMap, personsMap, execution.nodeStates, personsWithUsage,
    executionProgress, runningNodes, completedNodes, failedNodes,
    selectionOps, storeOperations, nodeOps, arrowOps, personOps, canvasHandlers, interactions, executionOps
  ]);
  
  return (
    <CanvasContext.Provider value={contextValue}>
      {children}
    </CanvasContext.Provider>
  );
}

/**
 * Primary hook to access both state and operations
 * This is the main hook most components should use
 */
export function useCanvas(): CanvasContextValue {
  const context = useContext(CanvasContext);
  if (!context) {
    throw new Error('useCanvas must be used within a CanvasProvider');
  }
  return context;
}

/**
 * Hook to access only canvas state (for components that don't need operations)
 * Use this when you only need to read state without performing actions
 */
export function useCanvasState(): CanvasState {
  const { state } = useCanvas();
  return state;
}

/**
 * Hook to access only canvas operations (for action-focused components)
 * Use this when you only need to perform actions without reading state
 */
export function useCanvasOperations(): CanvasOperations {
  const { operations } = useCanvas();
  return operations;
}

/**
 * Utility hook for checking if canvas is read-only
 * Convenience hook that combines readOnly and isExecuting states
 */
export function useIsCanvasReadOnly(): boolean {
  const { readOnly, isExecuting } = useCanvasState();
  return readOnly || isExecuting;
}