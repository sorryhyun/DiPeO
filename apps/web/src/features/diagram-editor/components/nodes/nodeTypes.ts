// Node types mapping for React Flow
import { NODE_CONFIGS_MAP } from '@/features/diagram-editor/config/nodes';
import ConfigurableNode from './ConfigurableNode';

// Create node types object for React Flow using NODE_CONFIGS
const nodeTypes = Object.fromEntries(
  Object.keys(NODE_CONFIGS_MAP).map((nodeType) => [
    nodeType,
    ConfigurableNode
  ])
);

// Note: Removed right-click drag wrapper to enable default left-click dragging
export default nodeTypes;