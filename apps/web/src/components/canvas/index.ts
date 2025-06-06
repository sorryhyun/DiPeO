// Consolidated node exports
import nodeTypes from './nodeTypes';
export { nodeTypes };

// Canvas components
export { DiagramCanvas } from './DiagramCanvas';
export { default as ContextMenu } from './ContextMenu';
export { CustomArrow } from './CustomArrow';
export { default as ConfigurableNode } from './ConfigurableNode';

// Export PersonClass separately as it's not a diagram node
export { default as PersonClass } from './PersonClass';

// Export BaseNode for direct usage
export { BaseNode } from './base/BaseNode';