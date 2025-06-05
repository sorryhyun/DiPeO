// Components
export { BaseNode } from './components/base/BaseNode';
export { GenericNode } from './components/base/GenericNode';
export { FlowHandle } from './components/base/FlowHandle';
export { default as nodeTypes } from './components/nodeTypes';
export { default as PersonClass } from './components/PersonClass';

// Types
export type { FlowHandleProps } from './components/base/FlowHandle';

// Hooks
export { useNodeDrag } from './hooks/useNodeDrag';
export { useNodeType } from './hooks/useNodeType';

// Utils
export {
  createNodeId,
  getNodeDisplayName,
  createHandleId
} from '@/common/utils/nodeHelpers';

export {
  validateNode,
  validateNodeData
} from './utils/nodeValidation';
export type { ValidationResult } from './utils/nodeValidation';


