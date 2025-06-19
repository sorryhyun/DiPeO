// Node types mapping for React Flow
import { UNIFIED_NODE_CONFIGS } from '@/core/config';
import ConfigurableNode from './ConfigurableNode';
import { applyRightClickDragToNodeTypes } from './withRightClickDrag';

// Create node types object for React Flow using NODE_CONFIGS
const baseNodeTypes = Object.fromEntries(
  Object.keys(UNIFIED_NODE_CONFIGS).map((nodeType) => [
    nodeType,
    ConfigurableNode
  ])
);

// Apply right-click drag functionality to all node types
const nodeTypes = applyRightClickDragToNodeTypes(baseNodeTypes);

export default nodeTypes;