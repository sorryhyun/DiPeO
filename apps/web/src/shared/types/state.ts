import { NodeID, ArrowID, HandleID } from '@/core/types';

export interface SelectionState {
  selectedNodes: Set<NodeID>;
  selectedArrows: Set<ArrowID>;
  selectedHandles: Set<HandleID>;
}

export interface InteractionState {
  isDragging: boolean;
  isConnecting: boolean;
  isPanning: boolean;
  isSelecting: boolean;
  hoveredNodeId: NodeID | null;
  hoveredHandleId: HandleID | null;
  hoveredArrowId: ArrowID | null;
}

export interface ViewportState {
  zoom: number;
  pan: { x: number; y: number };
  center: { x: number; y: number };
}

export interface UIState {
  selection: SelectionState;
  interaction: InteractionState;
  viewport: ViewportState;
}

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