// Consolidated node exports
import nodeTypes from './NodesGeneric';
export { nodeTypes };



// Export PersonClass separately as it's not a diagram node
export { default as PersonClass } from './PersonClass';

// Export BaseNode and GenericNode for direct usage
export { BaseNode } from '@/features/diagram/components/ui-components/BaseNode';
export { GenericNode } from '@/features/diagram/components/ui-components/GenericNode';