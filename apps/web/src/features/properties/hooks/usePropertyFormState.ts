import { useState, useEffect, useCallback, useRef } from 'react';

interface ValidationRule<T> {
  field: keyof T;
  validator: (value: any, formData: T) => string | null;
}

interface UsePropertyFormStateOptions<T> {
  validationRules?: ValidationRule<T>[];
  autoSave?: boolean;
  autoSaveDelay?: number;
  onSave?: (data: T) => Promise<void> | void;
  onError?: (error: string) => void;
}

export const usePropertyFormState = <T extends Record<string, any>>(
  initialData: T,
  entityId: string,
  entityType: 'node' | 'arrow' | 'person',
  options: UsePropertyFormStateOptions<T> = {}
) => {
  const {
    validationRules = [],
    autoSave = true,
    autoSaveDelay = 1000,
    onSave,
    onError
  } = options;

  const [formData, setFormData] = useState<T>(initialData);
  const [isDirty, setIsDirty] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const autoSaveTimeoutRef = useRef<NodeJS.Timeout>();
  const initialDataRef = useRef(initialData);

  // Update form data when initial data changes
  useEffect(() => {
    if (JSON.stringify(initialData) !== JSON.stringify(initialDataRef.current)) {
      setFormData(initialData);
      setIsDirty(false);
      setErrors({});
      initialDataRef.current = initialData;
    }
  }, [initialData]);

  // Validation function
  const validateField = useCallback((field: keyof T, value: any, currentFormData: T): string | null => {
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

  // Handle field changes
  const handleChange = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
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
      if (autoSave && onSave) {
        if (autoSaveTimeoutRef.current) {
          clearTimeout(autoSaveTimeoutRef.current);
        }
        
        autoSaveTimeoutRef.current = setTimeout(() => {
          if (!fieldError) {
            handleSave(newData);
          }
        }, autoSaveDelay);
      }
      
      return newData;
    });
  }, [validateField, autoSave, onSave, autoSaveDelay]);

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
      if (autoSave && onSave && !hasNewErrors) {
        if (autoSaveTimeoutRef.current) {
          clearTimeout(autoSaveTimeoutRef.current);
        }
        
        autoSaveTimeoutRef.current = setTimeout(() => {
          handleSave(newData);
        }, autoSaveDelay);
      }
      
      return newData;
    });
  }, [errors, validateField, autoSave, onSave, autoSaveDelay]);

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
    
    if (!onSave) return true;
    
    setIsSubmitting(true);
    
    try {
      await onSave(saveData);
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
  }, [formData, validateForm, onSave, onError]);

  // Handle form reset
  const reset = useCallback(() => {
    setFormData(initialDataRef.current);
    setIsDirty(false);
    setErrors({});
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);

  return {
    formData,
    isDirty,
    errors,
    isSubmitting,
    lastSaved,
    hasErrors: Object.keys(errors).length > 0,
    handleChange,
    updateFormData,
    handleSave: () => handleSave(),
    reset,
    validateForm: () => validateForm(formData)
  };
};