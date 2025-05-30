// Components
export { BaseNode } from './components/BaseNode';
export { default as NodesGeneric } from './components/NodesGeneric';
export { default as PersonClass } from './components/PersonClass';

// Hooks
export * from './hooks/useNodeOperations';
export * from './hooks/useNodeDrag';
export * from './hooks/useNodeConfig';

// Utils
export * from './utils/nodeHelpers';
export * from './utils/nodeValidation';

// Export nodeTypes for backward compatibility
import nodeTypes from './components/NodesGeneric';
export { nodeTypes };