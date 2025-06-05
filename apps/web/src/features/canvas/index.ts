import { lazy } from 'react';

// Main components
export { default as DiagramCanvas } from './components/DiagramCanvas';
export { default as PropertyDashboard } from './components/PropertyDashboard';

// Canvas components
export { CustomArrow } from './components/CustomArrow';

// Lazy load ContextMenu as it's only shown on right-click
export const ContextMenu = lazy(() => import('./components/ContextMenu'));

// Canvas hooks
export { useContextMenu } from './hooks/useContextMenu';
export { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

// Canvas utils
export {
  calculateNodeBounds,
  centerViewport,
  fitNodesToView,
  getOptimalNodePosition,
  roundPosition
} from './utils/canvasUtils';