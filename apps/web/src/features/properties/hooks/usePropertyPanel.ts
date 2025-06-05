import { useUpdateNodeData, useUpdateArrowData, useUpdatePerson } from '@/common/utils/storeSelectors';
import { usePropertyFormBase } from './usePropertyForm';

export function usePropertyPanel<T extends Record<string, unknown>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const updateNodeData = useUpdateNodeData();
  const updateArrowData = useUpdateArrowData();
  const updatePerson = useUpdatePerson();

  
  return usePropertyFormBase<T>(initialData, (updates: Partial<T>) => {
    if (entityType === 'node') {
      updateNodeData(entityId, updates as Record<string, unknown>);
    } else if (entityType === 'arrow') {
      updateArrowData(entityId, updates);
    } else {
      updatePerson(entityId, updates);
    }
  });
}