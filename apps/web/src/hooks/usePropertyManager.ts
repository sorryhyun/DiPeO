import { useState, useEffect, useCallback, useRef } from 'react';
import { isDraft, current } from 'immer';
import { useCanvasSelectors } from './useStoreSelectors';
import { type ApiKey } from '@/types';
import { useDiagramStore } from "@/stores";
import { useApiKeys } from "@/hooks/useApiKeys";

// Safe deep comparison using Immer to handle draft states
function safeDeepEqual(obj1: unknown, obj2: unknown): boolean {
  // Get the current value if it's an Immer draft
  const val1 = isDraft(obj1) ? current(obj1) : obj1;
  const val2 = isDraft(obj2) ? current(obj2) : obj2;
  
  // Handle primitives and null/undefined
  if (val1 === val2) return true;
  if (val1 == null || val2 == null) return false;
  if (typeof val1 !== 'object' || typeof val2 !== 'object') return false;
  
  // Arrays
  if (Array.isArray(val1) && Array.isArray(val2)) {
    if (val1.length !== val2.length) return false;
    for (let i = 0; i < val1.length; i++) {
      if (!safeDeepEqual(val1[i], val2[i])) return false;
    }
    return true;
  }
  
  // Objects
  if (Array.isArray(val1) || Array.isArray(val2)) return false;
  
  const keys1 = Object.keys(val1);
  const keys2 = Object.keys(val2);
  
  if (keys1.length !== keys2.length) return false;
  
  for (const key of keys1) {
    if (!keys2.includes(key)) return false;
    if (!safeDeepEqual((val1 as any)[key], (val2 as any)[key])) return false;
  }
  
  return true;
}

interface ValidationRule<T> {
  field: keyof T;
  validator: (value: unknown, formData: T) => string | null;
}

interface UsePropertyManagerOptions<T> {
  validationRules?: ValidationRule<T>[];
  autoSave?: boolean;
  autoSaveDelay?: number;
  onSave?: (data: T) => Promise<void> | void;
  onError?: (error: string) => void;
}

export const usePropertyManager = <T extends Record<string, unknown>>(
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  initialData: T,
  options: UsePropertyManagerOptions<T> = {}
) => {
  const {
    validationRules = [],
    autoSave = true,
    autoSaveDelay = 1000,
    onSave,
    onError
  } = options;

  // Store selectors
  const {updateArrow, updatePerson} = useDiagramStore();
  const { updateNode, isMonitorMode } = useCanvasSelectors();
  const { apiKeysList: apiKeys } = useApiKeys();

  // Form state
  const [formData, setFormData] = useState<T>(initialData);
  const [isDirty, setIsDirty] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const autoSaveTimeoutRef = useRef<number | undefined>(undefined);
  const initialDataRef = useRef(initialData);

  // Update form data when initial data changes
  useEffect(() => {
    if (!safeDeepEqual(initialData, initialDataRef.current)) {
      setFormData(initialData);
      setIsDirty(false);
      setErrors({});
      initialDataRef.current = initialData;
    }
  }, [initialData]);

  // Validation function
  const validateField = useCallback((field: keyof T, value: unknown, currentFormData: T): string | null => {
    const rule = validationRules.find(r => r.field === field);
    if (!rule) return null;
    return rule.validator(value, currentFormData);
  }, [validationRules]);

  // Validate all fields
  const validateForm = useCallback((data: T): Record<string, string> => {
    const newErrors: Record<string, string> = {};
    
    for (const rule of validationRules) {
      const error = rule.validator(data[rule.field], data);
      if (error) {
        newErrors[rule.field as string] = error;
      }
    }
    
    return newErrors;
  }, [validationRules]);

  // Auto-save function
  const autoSaveToStore = useCallback((data: T) => {
    if (isMonitorMode) return; // Don't auto-save in monitor mode
    
    try {
      if (entityType === 'node') {
        updateNode(entityId, data as Record<string, unknown>);
      } else if (entityType === 'arrow') {
        updateArrow(entityId, data);
      } else {
        updatePerson(entityId, data);
      }
      setLastSaved(new Date());
    } catch (error) {
      if (onError) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to auto-save';
        onError(errorMessage);
      }
    }
  }, [entityType, entityId, updateNode, updateArrow, updatePerson, isMonitorMode, onError]);

  // Handle field changes
  const updateField = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFormData(prev => {
      const newData = { ...prev, [field]: value };
      
      // Validate the changed field
      const fieldError = validateField(field, value, newData);
      setErrors(prevErrors => {
        const newErrors = { ...prevErrors };
        if (fieldError) {
          newErrors[field as string] = fieldError;
        } else {
          delete newErrors[field as string];
        }
        return newErrors;
      });
      
      setIsDirty(true);
      
      // Auto-save logic
      if (autoSave && !fieldError) {
        if (autoSaveTimeoutRef.current) {
          clearTimeout(autoSaveTimeoutRef.current);
        }
        
        autoSaveTimeoutRef.current = window.setTimeout(() => {
          if (onSave) {
            handleSave(newData);
          } else {
            autoSaveToStore(newData);
          }
        }, autoSaveDelay);
      }
      
      return newData;
    });
  }, [validateField, autoSave, autoSaveDelay, onSave, autoSaveToStore]);

  // Handle bulk updates
  const updateFormData = useCallback((updates: Partial<T>) => {
    setFormData(prev => {
      const newData = { ...prev, ...updates };
      
      // Validate all updated fields
      const newErrors = { ...errors };
      let hasNewErrors = false;
      
      for (const [field, value] of Object.entries(updates)) {
        const fieldError = validateField(field as keyof T, value, newData);
        if (fieldError) {
          newErrors[field] = fieldError;
          hasNewErrors = true;
        } else {
          delete newErrors[field];
        }
      }
      
      setErrors(newErrors);
      setIsDirty(true);
      
      // Auto-save if no errors
      if (autoSave && !hasNewErrors) {
        if (autoSaveTimeoutRef.current) {
          clearTimeout(autoSaveTimeoutRef.current);
        }
        
        autoSaveTimeoutRef.current = window.setTimeout(() => {
          if (onSave) {
            handleSave(newData);
          } else {
            autoSaveToStore(newData);
          }
        }, autoSaveDelay);
      }
      
      return newData;
    });
  }, [errors, validateField, autoSave, autoSaveDelay, onSave, autoSaveToStore]);

  // Handle manual save
  const handleSave = useCallback(async (dataToSave?: T) => {
    const saveData = dataToSave || formData;
    const formErrors = validateForm(saveData);
    
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      if (onError) {
        onError('Please fix validation errors before saving');
      }
      return false;
    }
    
    setIsSubmitting(true);
    
    try {
      if (onSave) {
        await onSave(saveData);
      } else {
        autoSaveToStore(saveData);
      }
      setIsDirty(false);
      setLastSaved(new Date());
      setErrors({});
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save';
      if (onError) {
        onError(errorMessage);
      }
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateForm, onSave, onError, autoSaveToStore]);

  // Handle form reset
  const reset = useCallback(() => {
    setFormData(initialDataRef.current);
    setIsDirty(false);
    setErrors({});
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
  }, []);

  // API key options for dropdowns
  const apiKeyOptions = useCallback(() => {
    return apiKeys.map((key: ApiKey) => ({
      value: key.id,
      label: `${key.service}: ${key.name}`,
      service: key.service
    }));
  }, [apiKeys]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);

  return {
    // Form data
    formData,
    isDirty,
    errors,
    isSubmitting,
    lastSaved,
    hasErrors: Object.keys(errors).length > 0,
    isReadOnly: isMonitorMode,
    
    // Actions
    updateField,
    updateFormData,
    save: () => handleSave(formData),
    reset,
    validateForm: () => validateForm(formData),
    
    // Utility
    apiKeyOptions: apiKeyOptions(),
  };
};