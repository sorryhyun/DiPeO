import { useConsolidatedDiagramStore } from '@/core/stores';
import { usePropertyFormBase } from './usePropertyForm';

export function usePropertyPanel<T extends Record<string, any>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const store = useConsolidatedDiagramStore();

  
  return usePropertyFormBase<T>(initialData, (updates: Partial<T>) => {
    console.log('[usePropertyPanel] Updating entity:', {
      entityId,
      entityType,
      updates,
      initialData
    });
    
    if (entityType === 'node') {
      store.updateNodeData(entityId, updates as Record<string, any>);
    } else if (entityType === 'arrow') {
      store.updateArrowData(entityId, updates as any);
    } else {
      console.log('[usePropertyPanel] Updating person via store.updatePerson');
      store.updatePerson(entityId, updates as any);
    }
  });
}