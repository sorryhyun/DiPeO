import { useArrowDataUpdater, useNodeDataUpdater } from '@/state/hooks/useStoreSelectors';
import { useUpdateNodeInternals } from '@xyflow/react';
import { getUnifiedNodeConfigsByReactFlowType } from '@/common/types';

export interface DiagramContextValue {
  // Arrow operations
  updateArrowData: ReturnType<typeof useArrowDataUpdater>;
  
  // Node operations  
  updateNodeData: ReturnType<typeof useNodeDataUpdater>;
  updateNodeInternals: ReturnType<typeof useUpdateNodeInternals>;
  nodeConfigs: ReturnType<typeof getUnifiedNodeConfigsByReactFlowType>;
  
  // Context menu data
  nodeTypes: string[];
  nodeLabels: Record<string, string>;
}