// Components
export { BaseNode } from './components/BaseNode';
export { GenericNode } from './components/GenericNode';
export { CustomArrow } from './components/Arrow';
export { default as Arrow } from './components/Arrow';
export { default as ContextMenu } from './components/ContextMenu';
export { FlowHandle } from './components/FlowHandle';
export type { FlowHandleProps } from './components/FlowHandle';

// Types from @repo/core-model
export type { 
  BaseNodeProps, 
  GenericNodeProps, 
  NodeConfig, 
  HandleConfig 
} from '@repo/core-model';
export type { ArrowData, CustomArrowProps } from './components/Arrow';
export type { ContextMenuProps } from './components/ContextMenu';

// Utils
export { createHandleId } from './utils/nodeHelpers';

// Hooks
export { useContextMenu } from './hooks/useContextMenu';
export type { ContextMenuState } from './hooks/useContextMenu';
export { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
export { usePropertyForm } from './hooks/usePropertyForm';