// Diagram UI package wrappers with store integration
export { CustomArrow } from '../components/CustomArrow';
export { default as ContextMenu } from '../components/ui-components/ContextMenu';

// Direct exports from local ui-components and hooks (no store integration needed)
export { FlowHandle } from '../components/ui-components/FlowHandle';
export { createHandleId } from '@/shared/utils/nodeHelpers';
export { useKeyboardShortcuts } from '../hooks/ui-hooks/useKeyboardShortcuts';
export { useContextMenu } from '../hooks/ui-hooks/useContextMenu';

// Node components removed - use direct imports from ../components/ui-components/
// export { BaseNode } from '../components/ui-components/BaseNode';
// export { GenericNode } from '../components/ui-components/GenericNode';

// Re-export types from local components
export type { FlowHandleProps } from '../components/ui-components/FlowHandle';
export type { BaseNodeProps, GenericNodeProps } from '../../../shared/types';