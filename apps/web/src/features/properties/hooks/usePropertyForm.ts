import { useConsolidatedDiagramStore } from '@/stores';
import { usePropertyForm as usePropertyFormBase } from '@repo/diagram-ui';

// Wrapper hook that integrates with app stores
export function usePropertyForm<T extends Record<string, any>>(
  nodeId: string,
  initialData: T
) {
  const updateNodeData = useConsolidatedDiagramStore(state => state.updateNodeData);
  return usePropertyFormBase(initialData, (updates) => {
    updateNodeData(nodeId, updates);
  });
}

// Re-export types
export type { PropertyFormHookResult } from '@repo/diagram-ui';