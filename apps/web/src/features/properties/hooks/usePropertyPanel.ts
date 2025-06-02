import { useConsolidatedDiagramStore } from '@/core/stores';
import { usePropertyFormBase } from './usePropertyForm';

export function usePropertyPanel<T extends Record<string, any>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T
) {
  const store = useConsolidatedDiagramStore();
  
  // Log when person property panel is accessed
  if (entityType === 'person') {
    console.log('[Person Property Panel] Initializing property panel for person:', {
      entityId,
      initialData: {
        label: (initialData as any).label,
        service: (initialData as any).service,
        apiKeyId: (initialData as any).apiKeyId,
        modelName: (initialData as any).modelName,
        systemPrompt: (initialData as any).systemPrompt ? `${((initialData as any).systemPrompt as string).substring(0, 50)}...` : undefined
      }
    });
  }
  
  return usePropertyFormBase<T>(initialData, (updates: Partial<T>) => {
    if (entityType === 'node') {
      store.updateNodeData(entityId, updates as Record<string, any>);
    } else if (entityType === 'arrow') {
      store.updateArrowData(entityId, updates as any);
    } else {
      // Log person updates
      console.log('[Person Property Panel] Updating person data:', {
        entityId,
        updates
      });
      store.updatePerson(entityId, updates as any);
    }
  });
}