import React, { createContext, useContext, ReactNode } from 'react';
import { useArrowDataUpdater, useNodeDataUpdater } from '@/hooks/useStoreSelectors';
import { useUpdateNodeInternals } from '@xyflow/react';
import { getUnifiedNodeConfigsByReactFlowType, UNIFIED_NODE_CONFIGS } from '@repo/core-model';

interface DiagramContextValue {
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

const DiagramContext = createContext<DiagramContextValue | null>(null);

export const useDiagramContext = () => {
  const context = useContext(DiagramContext);
  if (!context) {
    throw new Error('useDiagramContext must be used within a DiagramProvider');
  }
  return context;
};

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