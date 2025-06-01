import { useState, useEffect, useCallback } from 'react';
import { useConsolidatedDiagramStore } from '@/core/stores';

// Base property form hook
export function usePropertyFormBase<T extends Record<string, any>>(
  initialData: T,
  onUpdate?: (updates: Partial<T>) => void
) {
  const [formData, setFormData] = useState<T>(initialData);

  useEffect(() => {
    setFormData(initialData);
  }, [initialData]);

  const handleChange = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (onUpdate) {
      const update: Partial<T> = {};
      update[field] = value;
      onUpdate(update);
    }
  }, [onUpdate]);

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