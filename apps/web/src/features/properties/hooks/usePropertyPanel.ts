import { useNodeArrowStore, usePersonStore } from '@/state/stores';
import { usePropertyFormBase } from './usePropertyForm';

export function usePropertyPanel<T extends Record<string, unknown>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const nodeArrowStore = useNodeArrowStore();
  const personStore = usePersonStore();

  
  return usePropertyFormBase<T>(initialData, (updates: Partial<T>) => {
    if (entityType === 'node') {
      nodeArrowStore.updateNodeData(entityId, updates as Record<string, unknown>);
    } else if (entityType === 'arrow') {
      nodeArrowStore.updateArrowData(entityId, updates);
    } else {
      personStore.updatePerson(entityId, updates);
    }
  });
}