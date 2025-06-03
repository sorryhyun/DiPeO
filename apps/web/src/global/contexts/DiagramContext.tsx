import React, { createContext, ReactNode } from 'react';
import { useArrowDataUpdater, useNodeDataUpdater } from '@/global/hooks/useStoreSelectors';
import { useUpdateNodeInternals } from '@xyflow/react';
import { getUnifiedNodeConfigsByReactFlowType, UNIFIED_NODE_CONFIGS } from '@/shared/types';
import { DiagramContextValue } from './types';

const DiagramContext = createContext<DiagramContextValue | null>(null);
export { DiagramContext };

interface DiagramProviderProps {
  children: ReactNode;
}

export const DiagramProvider: React.FC<DiagramProviderProps> = ({ children }) => {
  const updateArrowData = useArrowDataUpdater();
  const updateNodeData = useNodeDataUpdater();
  const updateNodeInternals = useUpdateNodeInternals();
  const nodeConfigs = getUnifiedNodeConfigsByReactFlowType();
  
  // Extract node types and labels from UNIFIED_NODE_CONFIGS for context menu
  const nodeTypes = Object.keys(UNIFIED_NODE_CONFIGS);
  const nodeLabels = Object.fromEntries(
    Object.entries(UNIFIED_NODE_CONFIGS).map(([key, config]) => [key, config.label])
  );

  const value: DiagramContextValue = {
    updateArrowData,
    updateNodeData,
    updateNodeInternals,
    nodeConfigs,
    nodeTypes,
    nodeLabels,
  };

  return (
    <DiagramContext.Provider value={value}>
      {children}
    </DiagramContext.Provider>
  );
};