// Components
export { BaseNode } from './components/base/BaseNode';
export { GenericNode } from './components/base/GenericNode';
export { FlowHandle } from './components/base/FlowHandle';
export { default as NodesGeneric } from './components/NodesGeneric';
export { default as PersonClass } from './components/PersonClass';

// Types
export type { FlowHandleProps } from './components/base/FlowHandle';

// Hooks
export * from './hooks/useNodeOperations';
export * from './hooks/useNodeDrag';
export * from './hooks/useNodeType';

// Utils
export * from '@/shared/utils/nodeHelpers';
export * from './utils/nodeValidation';

// Export nodeTypes for React Flow
import NodesGeneric from './components/NodesGeneric';
export const nodeTypes = NodesGeneric;

