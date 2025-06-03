import { useState, useEffect, useCallback } from 'react';
import { useNodeArrowStore } from '@/global/stores';

// Base property form hook
export function usePropertyFormBase<T extends Record<string, any>>(
  initialData: T,
  onUpdate?: (updates: Partial<T>) => void
) {
  const [formData, setFormData] = useState<T>(initialData);

  useEffect(() => {
    setFormData(initialData);
  }, [initialData.id]); // Only reset when the entity ID changes

  const handleChange = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
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
  const updateNodeData = useNodeArrowStore(state => state.updateNodeData);
  return usePropertyFormBase(initialData, (updates) => {
    updateNodeData(nodeId, updates);
  });
}