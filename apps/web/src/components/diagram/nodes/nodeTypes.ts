// Node types mapping for React Flow
import { UNIFIED_NODE_CONFIGS } from '@/config';
import ConfigurableNode from './ConfigurableNode';

// Create node types object for React Flow using NODE_CONFIGS
const nodeTypes = Object.fromEntries(
  Object.keys(UNIFIED_NODE_CONFIGS).map((nodeType) => [
    nodeType,
    ConfigurableNode
  ])
);

export default nodeTypes;