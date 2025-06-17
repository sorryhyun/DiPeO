import { NodeID, ArrowID, HandleID } from '@/core/types';

/**
 * UI selection state
 */
export interface SelectionState {
  selectedNodes: Set<NodeID>;
  selectedArrows: Set<ArrowID>;
  selectedHandles: Set<HandleID>;
}

/**
 * UI interaction state
 */
export interface InteractionState {
  isDragging: boolean;
  isConnecting: boolean;
  isPanning: boolean;
  isSelecting: boolean;
  hoveredNodeId: NodeID | null;
  hoveredHandleId: HandleID | null;
  hoveredArrowId: ArrowID | null;
}

/**
 * Canvas viewport state
 */
export interface ViewportState {
  zoom: number;
  pan: { x: number; y: number };
  center: { x: number; y: number };
}

/**
 * Combined UI state
 */
export interface UIState {
  selection: SelectionState;
  interaction: InteractionState;
  viewport: ViewportState;
}

/**
 * Create initial UI state
 */
export function createInitialUIState(): UIState {
  return {
    selection: {
      selectedNodes: new Set(),
      selectedArrows: new Set(),
      selectedHandles: new Set()
    },
    interaction: {
      isDragging: false,
      isConnecting: false,
      isPanning: false,
      isSelecting: false,
      hoveredNodeId: null,
      hoveredHandleId: null,
      hoveredArrowId: null
    },
    viewport: {
      zoom: 1,
      pan: { x: 0, y: 0 },
      center: { x: 0, y: 0 }
    }
  };
}

/**
 * Selection helpers
 */
export function isNodeSelected(state: SelectionState, nodeId: NodeID): boolean {
  return state.selectedNodes.has(nodeId);
}

export function isArrowSelected(state: SelectionState, arrowId: ArrowID): boolean {
  return state.selectedArrows.has(arrowId);
}

export function clearSelection(state: SelectionState): SelectionState {
  return {
    selectedNodes: new Set(),
    selectedArrows: new Set(),
    selectedHandles: new Set()
  };
}