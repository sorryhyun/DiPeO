// Note: Canvas components have been moved to @/features/canvas
// Import them from there instead:
// - CustomArrow: @/features/canvas/components/CustomArrow
// - ContextMenu: @/features/canvas/components/ContextMenu
// - useKeyboardShortcuts: @/features/canvas/hooks/useKeyboardShortcuts
// - useContextMenu: @/features/canvas/hooks/useContextMenu

// Direct exports from shared utils
export { createHandleId } from '@/shared/utils/nodeHelpers';

// Node components moved to features/nodes/components/base/
// Use imports from @/features/nodes instead

// Re-export types from shared
export type { BaseNodeProps, GenericNodeProps } from '../../../shared/types';