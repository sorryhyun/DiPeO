/**
 * CanvasContext - Provides shared UI state and operations for canvas components
 * Eliminates prop drilling for commonly used canvas-related state and functions
 */

import React, { createContext, useContext, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useCanvas, useCanvasInteractions, useNodeOperations, useArrowOperations, usePersonOperations } from '@/features/diagram-editor/hooks';
import { useExecution } from '@/features/execution-monitor/hooks';
import { useDiagramData } from '@/shared/hooks/selectors/useDiagramData';
import { useUIState } from '@/shared/hooks/selectors/useUIState';
import { useExecutionData } from '@/shared/hooks/selectors/useExecutionData';
import { usePersonsData } from '@/shared/hooks/selectors/usePersonsData';
import type { Vec2, ArrowID, NodeID, PersonID, DomainNode, DomainArrow, DomainPerson } from '@dipeo/domain-models';
import type { DomainPersonType } from '@/__generated__/graphql';

interface CanvasUIState {
  // Selection state
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  selectedNodeIds: Set<NodeID>;
  
  // Canvas state
  activeCanvas: 'main' | 'execution' | 'memory' | 'preview' | 'monitor';
  readOnly: boolean;
  isExecuting: boolean;
  isPaused: boolean;
  
  // View state
  zoom: number;
  position: Vec2;
  
  // UI flags
  showGrid: boolean;
  showMinimap: boolean;
  showDebugInfo: boolean;
  
  // Additional UI state from useUIState
  activeModal: string | null;
  activePanel: 'properties' | 'conversation' | null;
  canvasMode: 'select' | 'pan' | 'zoom';
}

interface DiagramData {
  // Core diagram data
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  
  // Array versions for convenience
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  personsArray: DomainPerson[];
  
  // Metadata
  dataVersion: number;
  diagramName: string;
  diagramId: string | null;
}

interface ExecutionState {
  // Execution data from useExecutionData
  nodeStates: Map<NodeID, any>;
  progress: number;
  runningNodeCount: number;
  completedNodeCount: number;
  failedNodeCount: number;
}

interface CanvasOperations {
  // Selection operations
  selectNode: (nodeId: NodeID | null) => void;
  selectArrow: (arrowId: ArrowID | null) => void;
  selectPerson: (personId: PersonID | null) => void;
  selectMultipleNodes: (nodeIds: NodeID[]) => void;
  clearSelection: () => void;
  
  // Mode operations
  setReadOnly: (readOnly: boolean) => void;
  setCanvasMode: (mode: 'select' | 'pan' | 'zoom') => void;
  
  // Canvas operations from focused hooks
  canvas: ReturnType<typeof useCanvas>;
  interactions: ReturnType<typeof useCanvasInteractions>;
  nodeOps: ReturnType<typeof useNodeOperations>;
  arrowOps: ReturnType<typeof useArrowOperations>;
  personOps: ReturnType<typeof usePersonOperations>;
  executionOps: ReturnType<typeof useExecution>;
  
  // Store operations for direct access
  store: {
    clearDiagram: () => void;
    clearAll: () => void;
    validateDiagram: () => { isValid: boolean; errors: string[] };
  };
}

interface CanvasContextValue extends CanvasUIState, CanvasOperations {
  // Diagram data
  diagram: DiagramData;
  
  // Execution state
  execution: ExecutionState;
  
  // Person data with usage stats  
  personsWithUsage: Array<DomainPerson & { nodeCount: number }>;
}

const CanvasContext = createContext<CanvasContextValue | null>(null);

/**
 * CanvasProvider - Provides canvas context to children
 */
export function CanvasProvider({ children }: { children: React.ReactNode }) {
  // Get UI state from store
  const uiState = useUnifiedStore(
    useShallow(state => ({
      // Derive selection state from unified selection model
      selectedNodeId: state.selectedType === 'node' ? (state.selectedId as NodeID) : null,
      selectedArrowId: state.selectedType === 'arrow' ? (state.selectedId as ArrowID) : null,
      selectedPersonId: state.selectedType === 'person' ? (state.selectedId as PersonID) : null,
      multiSelectedIds: state.multiSelectedIds,
      selectedType: state.selectedType,
      activeCanvas: state.activeCanvas,
      readOnly: state.readOnly,
      isExecuting: state.execution.isRunning,
      isPaused: state.execution.isPaused,
      zoom: state.zoom,
      position: state.position,
      showGrid: state.showGrid,
      showMinimap: state.showMinimap,
      showDebugInfo: state.showDebugInfo,
      activeModal: state.activeModal,
      activePanel: state.dashboardTab === 'properties' ? 'properties' as const : null,
      canvasMode: state.canvasMode
    }))
  );

  // Create selectedNodeIds Set from multiSelectedIds
  const selectedNodeIds = useMemo(() => {
    const nodeIds = new Set<NodeID>();
    if (uiState.selectedType === 'node') {
      uiState.multiSelectedIds.forEach(id => {
        nodeIds.add(id as NodeID);
      });
    }
    return nodeIds;
  }, [uiState.multiSelectedIds, uiState.selectedType]);

  // Get selection operations from store - extract functions directly
  const select = useUnifiedStore(state => state.select);
  const clearSelection = useUnifiedStore(state => state.clearSelection);
  const multiSelect = useUnifiedStore(state => state.multiSelect);
  const setReadOnly = useUnifiedStore(state => state.setReadOnly);
  const setCanvasMode = useUnifiedStore(state => state.setCanvasMode);
  
  // Get store operations for direct access
  const clearDiagram = useUnifiedStore(state => state.clearDiagram);
  const clearAll = useUnifiedStore(state => state.clearAll);
  const validateDiagram = useUnifiedStore(state => state.validateDiagram);
  
  // Create stable operation wrappers
  const selectionOps = React.useMemo(() => ({
    selectNode: (nodeId: NodeID | null) => {
      if (nodeId) {
        select(nodeId, 'node');
      } else {
        clearSelection();
      }
    },
    selectArrow: (arrowId: ArrowID | null) => {
      if (arrowId) {
        select(arrowId, 'arrow');
      } else {
        clearSelection();
      }
    },
    selectPerson: (personId: PersonID | null) => {
      if (personId) {
        select(personId, 'person');
      } else {
        clearSelection();
      }
    },
    selectMultipleNodes: (nodeIds: NodeID[]) => {
      multiSelect(nodeIds, 'node');
    },
    clearSelection,
    setReadOnly,
    setCanvasMode,
  }), [select, clearSelection, multiSelect, setReadOnly, setCanvasMode]);
  
  // Create stable store operations object
  const storeOps = React.useMemo(() => ({
    clearDiagram,
    clearAll,
    validateDiagram,
  }), [clearDiagram, clearAll, validateDiagram]);

  // Get hook-based operations
  const canvas = useCanvas();
  const interactions = useCanvasInteractions();
  const nodeOps = useNodeOperations();
  const arrowOps = useArrowOperations();
  const personOps = usePersonOperations();
  const executionOps = useExecution();
  
  // Get diagram data
  const diagramData = useDiagramData();
  const executionData = useExecutionData();
  const { personsArray, persons: personsMap } = usePersonsData();
  
  // Calculate persons with usage stats
  const nodePersonUsage = useMemo(() => {
    const usageMap = new Map<PersonID, number>();
    diagramData.nodesArray.forEach(node => {
      if ((node.type === 'person_job' || node.type === 'person_batch_job') && node.data?.person) {
        const personId = node.data.person as PersonID;
        usageMap.set(personId, (usageMap.get(personId) || 0) + 1);
      } else if ((node.type === 'person_job' || node.type === 'person_batch_job') && node.data?.personId) {
        // Also check personId for compatibility
        const personId = node.data.personId as PersonID;
        usageMap.set(personId, (usageMap.get(personId) || 0) + 1);
      }
    });
    return usageMap;
  }, [diagramData.nodesArray]);
  
  const personsWithUsage = useMemo(() => {
    // Type assertion helper to ensure GraphQL persons are compatible with domain model
    const toDomainPerson = (person: DomainPersonType): DomainPerson => {
      return {
        ...person,
        llm_config: {
          ...person.llm_config,
          api_key_id: person.llm_config.api_key_id || ''
        }
      } as DomainPerson;
    };
    
    return personsArray.map(person => ({
      ...toDomainPerson(person as any),
      nodeCount: nodePersonUsage.get(person.id as PersonID) || 0
    }));
  }, [personsArray, nodePersonUsage]);
  
  // Get diagram metadata from store
  const diagramMetadata = useUnifiedStore(
    useShallow(state => ({
      diagramName: state.diagramName,
      diagramId: state.diagramId,
    }))
  );

  // Memoize context value
  const contextValue = useMemo<CanvasContextValue>(
    () => ({
      // UI state
      ...uiState,
      selectedNodeIds, // Override with the memoized Set
      
      // Operations
      ...selectionOps,
      store: storeOps,
      canvas,
      interactions,
      nodeOps,
      arrowOps,
      personOps,
      executionOps,
      
      // Diagram data
      diagram: {
        nodes: diagramData.nodes,
        arrows: diagramData.arrows,
        persons: new Map(Array.from(personsMap.entries()).map(([id, person]) => [
          id,
          {
            ...person,
            llm_config: {
              ...person.llm_config,
              api_key_id: person.llm_config.api_key_id || ''
            }
          } as DomainPerson
        ])),
        nodesArray: diagramData.nodesArray,
        arrowsArray: diagramData.arrowsArray,
        personsArray: personsWithUsage.map(({ nodeCount: _nodeCount, ...person }) => person),
        dataVersion: diagramData.dataVersion,
        diagramName: diagramMetadata.diagramName,
        diagramId: diagramMetadata.diagramId,
      },
      
      // Execution state
      execution: {
        nodeStates: executionData.nodeStates,
        progress: executionData.progress,
        runningNodeCount: executionData.runningNodeCount,
        completedNodeCount: executionData.completedNodeCount,
        failedNodeCount: executionData.failedNodeCount,
      },
      
      // Person data with usage
      personsWithUsage,
    }),
    [
      uiState, selectedNodeIds, selectionOps, storeOps, canvas, interactions, 
      nodeOps, arrowOps, personOps, executionOps, diagramData, executionData, 
      personsMap, personsWithUsage, diagramMetadata
    ]
  );

  return (
    <CanvasContext.Provider value={contextValue}>
      {children}
    </CanvasContext.Provider>
  );
}

/**
 * useCanvasContext - Hook to access canvas context
 * @throws Error if used outside of CanvasProvider
 */
export function useCanvasContext(): CanvasContextValue {
  const context = useContext(CanvasContext);
  if (!context) {
    throw new Error('useCanvasContext must be used within a CanvasProvider');
  }
  return context;
}

/**
 * useCanvasUIState - Hook to access only UI state (for components that don't need operations)
 */
export function useCanvasUIState(): CanvasUIState {
  const context = useCanvasContext();
  return {
    selectedNodeId: context.selectedNodeId,
    selectedArrowId: context.selectedArrowId,
    selectedPersonId: context.selectedPersonId,
    selectedNodeIds: context.selectedNodeIds,
    activeCanvas: context.activeCanvas,
    readOnly: context.readOnly,
    isExecuting: context.isExecuting,
    isPaused: context.isPaused,
    zoom: context.zoom,
    position: context.position,
    showGrid: context.showGrid,
    showMinimap: context.showMinimap,
    showDebugInfo: context.showDebugInfo,
    activeModal: context.activeModal,
    activePanel: context.activePanel,
    canvasMode: context.canvasMode,
  };
}

/**
 * useCanvasOperationsContext - Hook to access only operations (for action-focused components)
 */
export function useCanvasOperationsContext() {
  const context = useCanvasContext();
  return {
    selectNode: context.selectNode,
    selectArrow: context.selectArrow,
    selectPerson: context.selectPerson,
    selectMultipleNodes: context.selectMultipleNodes,
    clearSelection: context.clearSelection,
    setReadOnly: context.setReadOnly,
    canvas: context.canvas,
    interactions: context.interactions,
    nodeOps: context.nodeOps,
    arrowOps: context.arrowOps,
    personOps: context.personOps,
    executionOps: context.executionOps,
  };
}

/**
 * useCanvasSelection - Hook for components that only need selection state
 */
export function useCanvasSelection() {
  const context = useCanvasContext();
  return {
    selectedNodeId: context.selectedNodeId,
    selectedArrowId: context.selectedArrowId,
    selectedPersonId: context.selectedPersonId,
    selectedNodeIds: context.selectedNodeIds,
    selectNode: context.selectNode,
    selectArrow: context.selectArrow,
    selectPerson: context.selectPerson,
    selectMultipleNodes: context.selectMultipleNodes,
    clearSelection: context.clearSelection,
  };
}

/**
 * useCanvasReadOnly - Hook for components that need to check read-only state
 */
export function useCanvasReadOnly(): boolean {
  const { readOnly, isExecuting } = useCanvasUIState();
  return readOnly || isExecuting;
}

/**
 * useCanvasDiagramData - Hook for components that need diagram data
 */
export function useCanvasDiagramData(): DiagramData {
  const context = useCanvasContext();
  return context.diagram;
}

/**
 * useCanvasExecutionState - Hook for components that need execution state
 */
export function useCanvasExecutionState(): ExecutionState {
  const context = useCanvasContext();
  return context.execution;
}

/**
 * useCanvasStore - Hook for components that need direct store operations
 */
export function useCanvasStore() {
  const context = useCanvasContext();
  return context.store;
}

/**
 * useCanvasPersons - Hook for components that need person data with usage stats
 */
export function useCanvasPersons() {
  const context = useCanvasContext();
  return context.personsWithUsage;
}