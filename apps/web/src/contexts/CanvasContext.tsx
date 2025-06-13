/**
 * CanvasContext - Provides shared UI state and operations for canvas components
 * Eliminates prop drilling for commonly used canvas-related state and functions
 */

import React, { createContext, useContext, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/stores/unifiedStore';
import { useCanvasOperations } from '@/hooks/useCanvasOperations';
import { useDiagramOperations } from '@/hooks/useDiagramOperations';
import { useExecutionOperations } from '@/hooks/useExecutionOperations';
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
  canvasOps: ReturnType<typeof useCanvasOperations>;
  diagramOps: ReturnType<typeof useDiagramOperations>;
  executionOps: ReturnType<typeof useExecutionOperations>;
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
      selectedNodeId: state.selectedNodeId,
      selectedArrowId: state.selectedArrowId,
      selectedPersonId: state.selectedPersonId,
      selectedNodeIds: state.selectedNodeIds,
      activeCanvas: state.activeCanvas,
      readOnly: state.readOnly,
      isExecuting: state.isExecuting,
      isPaused: state.isPaused,
      zoom: state.canvasPosition?.zoom ?? 1,
      position: state.canvasPosition?.position ?? { x: 0, y: 0 },
      showGrid: state.settings?.showGrid ?? true,
      showMinimap: state.settings?.showMinimap ?? false,
      showDebugInfo: state.settings?.showDebugInfo ?? false,
    }))
  );

  // Get selection operations from store
  const selectionOps = useUnifiedStore(
    useShallow(state => ({
      selectNode: state.selectNode,
      selectArrow: state.selectArrow,
      selectPerson: state.selectPerson,
      selectMultipleNodes: state.selectMultipleNodes,
      clearSelection: state.clearSelection,
      setReadOnly: state.setReadOnly,
    }))
  );

  // Get hook-based operations
  const canvasOps = useCanvasOperations();
  const diagramOps = useDiagramOperations();
  const executionOps = useExecutionOperations();

  // Memoize context value
  const contextValue = useMemo<CanvasContextValue>(
    () => ({
      // UI state
      ...uiState,
      
      // Operations
      ...selectionOps,
      canvasOps,
      diagramOps,
      executionOps,
    }),
    [uiState, selectionOps, canvasOps, diagramOps, executionOps]
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
 * useCanvasOperations - Hook to access only operations (for action-focused components)
 */
export function useCanvasOperations() {
  const context = useCanvasContext();
  return {
    selectNode: context.selectNode,
    selectArrow: context.selectArrow,
    selectPerson: context.selectPerson,
    selectMultipleNodes: context.selectMultipleNodes,
    clearSelection: context.clearSelection,
    setReadOnly: context.setReadOnly,
    canvasOps: context.canvasOps,
    diagramOps: context.diagramOps,
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