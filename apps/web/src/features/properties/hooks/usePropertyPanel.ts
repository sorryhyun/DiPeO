import { useConsolidatedDiagramStore } from '@/core/stores';
import { usePropertyFormBase } from './usePropertyForm';

export function usePropertyPanel<T extends Record<string, any>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const store = useConsolidatedDiagramStore();
  
  return usePropertyFormBase<T>(initialData, (updates: Partial<T>) => {
    if (entityType === 'node') {
      store.updateNodeData(entityId, updates as Record<string, any>);
    } else if (entityType === 'arrow') {
      store.updateArrowData(entityId, updates as any);
    } else {
      store.updatePerson(entityId, updates as any);
    }
  });
}