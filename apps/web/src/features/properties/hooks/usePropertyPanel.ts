import { useConsolidatedDiagramStore } from '@/core/stores';
import { usePropertyForm as usePropertyFormBase } from '../../diagram/hooks/ui-hooks/usePropertyForm';

export function usePropertyPanel<T extends Record<string, any>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const store = useConsolidatedDiagramStore();
  
  const updateFn = entityType === 'node' 
    ? store.updateNodeData
    : entityType === 'arrow' 
    ? store.updateArrowData 
    : store.updatePerson;
    
  return usePropertyFormBase(initialData, (updates) => {
    updateFn(entityId, updates);
  });
}