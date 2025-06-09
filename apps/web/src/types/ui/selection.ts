import { NodeID, ArrowID, HandleID } from '../branded';

/**
 * Selection types
 */
export type SelectableType = 'node' | 'arrow' | 'handle';

/**
 * Selection item
 */
export interface SelectionItem {
  type: SelectableType;
  id: string;
}

/**
 * Selection bounds for box selection
 */
export interface SelectionBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Multi-selection action
 */
export type SelectionAction = 
  | { type: 'select'; items: SelectionItem[] }
  | { type: 'deselect'; items: SelectionItem[] }
  | { type: 'toggle'; items: SelectionItem[] }
  | { type: 'clear' }
  | { type: 'selectAll' };

/**
 * Selection event
 */
export interface SelectionEvent {
  action: SelectionAction;
  modifiers: {
    shift: boolean;
    ctrl: boolean;
    meta: boolean;
  };
  timestamp: number;
}

/**
 * Convert typed IDs to selection items
 */
export function nodeToSelectionItem(id: NodeID): SelectionItem {
  return { type: 'node', id };
}

export function arrowToSelectionItem(id: ArrowID): SelectionItem {
  return { type: 'arrow', id };
}

export function handleToSelectionItem(id: HandleID): SelectionItem {
  return { type: 'handle', id };
}

/**
 * Check if point is within bounds
 */
export function isPointInBounds(
  point: { x: number; y: number },
  bounds: SelectionBounds
): boolean {
  return (
    point.x >= bounds.x &&
    point.x <= bounds.x + bounds.width &&
    point.y >= bounds.y &&
    point.y <= bounds.y + bounds.height
  );
}

/**
 * Calculate selection bounds from two points
 */
export function calculateSelectionBounds(
  start: { x: number; y: number },
  end: { x: number; y: number }
): SelectionBounds {
  const x = Math.min(start.x, end.x);
  const y = Math.min(start.y, end.y);
  const width = Math.abs(end.x - start.x);
  const height = Math.abs(end.y - start.y);

  return { x, y, width, height };
}