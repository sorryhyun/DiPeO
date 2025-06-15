/**
 * CanvasContext - Provides shared UI state and operations for canvas components
 * Eliminates prop drilling for commonly used canvas-related state and functions
 */

import React, { createContext, useContext, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/stores/unifiedStore';
import { useCanvasOperations as useCanvasOps } from '@/hooks/useCanvasOperations';
import { useExecutionProvider } from '@/hooks/useExecutionProvider';
import type { NodeID, ArrowID, PersonID, Vec2 } from '@/types';

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
  
  // Canvas operations from hooks
  canvasOps: ReturnType<typeof useCanvasOps>;
  executionOps: ReturnType<typeof useExecutionProvider>;
}

interface CanvasContextValue extends CanvasUIState, CanvasOperations {}

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
      isPaused: false, // TODO: Add isPaused to execution state
      zoom: 1, // TODO: Get from React Flow instance
      position: { x: 0, y: 0 }, // TODO: Get from React Flow instance
      showGrid: true, // TODO: Add to settings
      showMinimap: false, // TODO: Add to settings
      showDebugInfo: false, // TODO: Add to settings
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

  // Get selection operations from store
  const selectionOps = useUnifiedStore(
    useShallow(state => ({
      selectNode: (nodeId: NodeID | null) => {
        if (nodeId) {
          state.select(nodeId, 'node');
        } else {
          state.clearSelection();
        }
      },
      selectArrow: (arrowId: ArrowID | null) => {
        if (arrowId) {
          state.select(arrowId, 'arrow');
        } else {
          state.clearSelection();
        }
      },
      selectPerson: (personId: PersonID | null) => {
        if (personId) {
          state.select(personId, 'person');
        } else {
          state.clearSelection();
        }
      },
      selectMultipleNodes: (nodeIds: NodeID[]) => {
        state.multiSelect(nodeIds, 'node');
      },
      clearSelection: state.clearSelection,
      setReadOnly: state.setReadOnly,
    }))
  );

  // Get hook-based operations
  const canvasOps = useCanvasOps();
  const executionOps = useExecutionProvider();

  // Memoize context value
  const contextValue = useMemo<CanvasContextValue>(
    () => ({
      // UI state
      ...uiState,
      selectedNodeIds, // Override with the memoized Set
      
      // Operations
      ...selectionOps,
      canvasOps,
      executionOps,
    }),
    [uiState, selectedNodeIds, selectionOps, canvasOps, executionOps]
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
    canvasOps: context.canvasOps,
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