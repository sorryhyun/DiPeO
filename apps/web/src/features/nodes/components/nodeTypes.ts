// Node types mapping for React Flow
import { UNIFIED_NODE_CONFIGS } from '@/common/types';
import UniversalNode from './UniversalNode';

// Create node types object for React Flow using UNIFIED_NODE_CONFIGS
const nodeTypes = Object.fromEntries(
  Object.entries(UNIFIED_NODE_CONFIGS).map(([_, config]) => [
    config.reactFlowType,
    UniversalNode
  ])
);

export default nodeTypes;