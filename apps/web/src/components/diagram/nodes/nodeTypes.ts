// Node types mapping for React Flow
import { getAllNodeConfigs } from '@/features/diagram-editor/config/nodes';
import ConfigurableNode from './ConfigurableNode';

// Create node types object for React Flow using NODE_CONFIGS
const nodeTypes = Object.fromEntries(
  Array.from(getAllNodeConfigs().keys()).map((nodeType) => [
    nodeType,
    ConfigurableNode
  ])
);

// Note: Removed right-click drag wrapper to enable default left-click dragging
export default nodeTypes;