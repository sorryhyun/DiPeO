// Diagram UI package wrappers with store integration
export { CustomArrow } from '../components/CustomArrow';
export { default as ContextMenu } from '../components/ui-components/ContextMenu';

// Direct exports from local ui-components and hooks (no store integration needed)
export { createHandleId } from '@/shared/utils/nodeHelpers';
export { useKeyboardShortcuts } from '../hooks/ui-hooks/useKeyboardShortcuts';
export { useContextMenu } from '../hooks/ui-hooks/useContextMenu';

// Node components moved to features/nodes/components/base/
// Use imports from @/features/nodes instead

// Re-export types from shared
export type { BaseNodeProps, GenericNodeProps } from '../../../shared/types';