// Canvas UI wrappers with store integration
import { lazy } from 'react';

export { CustomArrow } from '../components/CustomArrow';

// Lazy load ContextMenu as it's only shown on right-click
export const ContextMenu = lazy(() => import('../components/ContextMenu'));

// Direct exports from hooks
export { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
export { useContextMenu } from '../hooks/useContextMenu';