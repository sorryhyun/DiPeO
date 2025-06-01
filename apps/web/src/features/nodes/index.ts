// Components
export { BaseNode } from '@/features/diagram/components/ui-components/BaseNode';
export { default as NodesGeneric } from './components/NodesGeneric';
export { default as PersonClass } from './components/PersonClass';

// Hooks
export * from './hooks/useNodeOperations';
export * from './hooks/useNodeDrag';
export * from './hooks/useNodeConfig';

// Utils
export * from '@/shared/utils/nodeHelpers';
export * from './utils/nodeValidation';

// Export nodeTypes for React Flow
import NodesGeneric from './components/NodesGeneric';
export const nodeTypes = NodesGeneric;

