import { useDiagramStore } from '@/state/stores';
import { usePropertyFormBase } from './usePropertyForm';

export function usePropertyPanel<T extends Record<string, unknown>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const diagramStore = useDiagramStore();

  
  return usePropertyFormBase<T>(initialData, (updates: Partial<T>) => {
    if (entityType === 'node') {
      diagramStore.updateNodeData(entityId, updates as Record<string, unknown>);
    } else if (entityType === 'arrow') {
      diagramStore.updateArrowData(entityId, updates);
    } else {
      diagramStore.updatePerson(entityId, updates);
    }
  });
}