import { useState, useEffect, useCallback } from 'react';
import { useConsolidatedDiagramStore } from '@/core/stores';

// Base property form hook
export function usePropertyFormBase<T extends Record<string, any>>(
  initialData: T,
  onUpdate?: (updates: Partial<T>) => void
) {
  const [formData, setFormData] = useState<T>(initialData);

  useEffect(() => {
    // Log when initialData changes (for person property panel)
    if ((initialData as any).type === 'person') {
      console.log('[Person Property Panel] usePropertyFormBase - initialData changed:', {
        service: (initialData as any).service,
        apiKeyId: (initialData as any).apiKeyId,
        modelName: (initialData as any).modelName,
        id: (initialData as any).id,
        timestamp: Date.now()
      });
    }
    setFormData(initialData);
  }, [JSON.stringify(initialData)]); // Use JSON.stringify to detect deep changes

  const handleChange = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFormData(prev => {
      // Log state updates for person property panel
      if ((prev as any).type === 'person' && (field === 'service' || field === 'apiKeyId' || field === 'modelName')) {
        console.log('[Person Property Panel] usePropertyFormBase - handleChange called:', {
          field,
          oldValue: prev[field],
          newValue: value
        });
      }
      
      return { ...prev, [field]: value };
    });
    
    if (onUpdate) {
      const update: Partial<T> = {};
      update[field] = value;
      onUpdate(update);
    }
  }, [onUpdate]); // Remove formData from dependencies to avoid stale closure

  const updateFormData = useCallback((updates: Partial<T>) => {
    setFormData(prev => ({ ...prev, ...updates }));
    if (onUpdate) {
      onUpdate(updates);
    }
  }, [onUpdate]);

  return { formData, handleChange, updateFormData };
}

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