import { useConsolidatedDiagramStore } from '@/shared/stores';
import { usePropertyForm as usePropertyFormBase } from '../../diagram/hooks/ui-hooks/usePropertyForm';

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
// Type inference will handle the return type automatically