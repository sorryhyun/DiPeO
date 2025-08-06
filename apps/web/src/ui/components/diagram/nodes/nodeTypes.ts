// Node types mapping for React Flow
import { getAllNodeConfigs } from '@/domain/diagram/config/nodes';
import ConfigurableNode from './ConfigurableNode';
// Import the registry to ensure node configs are loaded
import '@/__generated__/nodeRegistry';

// Create node types object for React Flow using NODE_CONFIGS
const nodeTypes = Object.fromEntries(
  Array.from(getAllNodeConfigs().entries()).map(([nodeType, config]) => {
    // Ensure we use the string value of the node type
    const typeStr = typeof nodeType === 'string' ? nodeType : String(nodeType);
    return [typeStr, ConfigurableNode];
  })
);

// Note: Removed right-click drag wrapper to enable default left-click dragging
export default nodeTypes;