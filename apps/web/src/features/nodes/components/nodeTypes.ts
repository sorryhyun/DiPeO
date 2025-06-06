// Node types mapping for React Flow
import { UNIFIED_NODE_CONFIGS } from '../../../types';
import ConfigurableNode from './ConfigurableNode';

// Create node types object for React Flow using UNIFIED_NODE_CONFIGS
const nodeTypes = Object.fromEntries(
  Object.entries(UNIFIED_NODE_CONFIGS).map(([_, config]) => [
    config.reactFlowType,
    ConfigurableNode
  ])
);

export default nodeTypes;