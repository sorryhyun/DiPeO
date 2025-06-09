import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { isDraft, current } from 'immer';
import { useQueries } from '@tanstack/react-query';
import { 
  useCanvasSelectors, 
  useNodeDataUpdater, 
  useArrowDataUpdater, 
  usePersonDataUpdater 
} from './useStoreSelectors';
import { useEvent } from './useEvent';
import type { DomainApiKey } from '@/types/domain/api-key';
import type { PanelConfig, PanelFieldConfig } from '@/types/ui/panel';
import type { NodeID, ArrowID, PersonID } from '@/types/branded';
import { nodeId, arrowId, personId } from '@/types/branded';
import { useUnifiedStore } from "@/stores/useUnifiedStore";

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

interface ValidationRule<T extends Record<string, unknown> = Record<string, unknown>> {
  field: keyof T;
  validator: (value: unknown, formData: T) => string | null;
}

interface ProcessedField {
  field: PanelFieldConfig;
  options?: Array<{ value: string; label: string }>;
  isLoading?: boolean;
  error?: Error | null;
}

interface UsePropertyManagerOptions<T extends Record<string, unknown> = Record<string, unknown>> {
  validationRules?: ValidationRule<T>[];
  autoSave?: boolean;
  autoSaveDelay?: number;
  onSave?: (data: T) => Promise<void> | void;
  onError?: (error: string) => void;
  panelConfig?: PanelConfig<T>;
}

export const usePropertyManager = <T extends Record<string, unknown> = Record<string, unknown>>(
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
  const updateNode = useNodeDataUpdater();
  const updateArrow = useArrowDataUpdater();
  const updatePerson = usePersonDataUpdater();
  const { isMonitorMode } = useCanvasSelectors();
  const { apiKeys } = useUnifiedStore();

  // Form state
  const [formData, setFormData] = useState<T>(initialData);
  const [isDirty, setIsDirty] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const autoSaveTimeoutRef = useRef<number | undefined>(undefined);
  const initialDataRef = useRef(initialData);

  // Combined effect for initialization and cleanup
  useEffect(() => {
    // Update form data when initial data changes
    if (!safeDeepEqual(initialData, initialDataRef.current)) {
      setFormData(initialData);
      setIsDirty(false);
      setErrors({});
      initialDataRef.current = initialData;
    }

    // Cleanup timeout on unmount
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [initialData]);

  // Validation function - no need for useCallback since validationRules is stable
  const validateField = (field: keyof T, value: unknown, currentFormData: T): string | null => {
    const rule = validationRules.find(r => r.field === field);
    if (!rule) return null;
    return rule.validator(value, currentFormData);
  };

  // Validate all fields
  const validateForm = (data: T): Record<string, string> => {
    const newErrors: Record<string, string> = {};
    
    for (const rule of validationRules) {
      const error = rule.validator(data[rule.field], data);
      if (error) {
        newErrors[rule.field as string] = error;
      }
    }
    
    return newErrors;
  };

  // Auto-save function - using useEvent for stable reference
  const autoSaveToStore = useEvent((data: T) => {
    if (isMonitorMode) return; // Don't auto-save in monitor mode
    
    try {
      if (entityType === 'node') {
        updateNode(nodeId(entityId), data as Record<string, unknown>);
      } else if (entityType === 'arrow') {
        updateArrow(arrowId(entityId), data);
      } else {
        updatePerson(personId(entityId), data);
      }
      setLastSaved(new Date());
    } catch (error) {
      if (onError) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to auto-save';
        onError(errorMessage);
      }
    }
  });

  // Handle field changes with batched state updates - using useEvent for stable reference
  const updateField = useEvent(<K extends keyof T>(field: K, value: T[K]) => {
    // Batch all state updates together
    const newData = { ...formData, [field]: value };
    const fieldError = validateField(field, value, newData);
    
    // Update all state at once
    setFormData(newData);
    setErrors(prevErrors => {
      if (fieldError) {
        return { ...prevErrors, [field as string]: fieldError };
      } else {
        const { [field as string]: _, ...rest } = prevErrors;
        return rest;
      }
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
  });

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

  // Handle manual save - using useEvent for stable reference
  const handleSave = useEvent(async (dataToSave?: T) => {
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
  });

  // Handle form reset
  const reset = useCallback(() => {
    setFormData(initialDataRef.current);
    setIsDirty(false);
    setErrors({});
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
  }, []);

  // API key options for dropdowns - memoize instead of useCallback
  const apiKeyOptions = useMemo(() => {
    return Array.from(apiKeys.values()).map((key: DomainApiKey) => ({
      value: key.id,
      label: `${key.service}: ${key.name}`,
      service: key.service
    }));
  }, [apiKeys]);

  // Panel schema functionality
  const fields = useMemo(() => {
    if (!options.panelConfig) return [];
    const config = options.panelConfig;
    
    const flattenFields = (fields: PanelFieldConfig[]): PanelFieldConfig[] => {
      const result: PanelFieldConfig[] = [];
      
      fields.forEach(field => {
        if (field.type === 'row' && field.fields) {
          result.push(...flattenFields(field.fields));
        } else {
          result.push(field);
        }
      });
      
      return result;
    };
    
    let allFields: PanelFieldConfig[] = [];
    
    if (config.fields) {
      allFields = allFields.concat(flattenFields(config.fields));
    }
    if (config.leftColumn) {
      allFields = allFields.concat(flattenFields(config.leftColumn));
    }
    if (config.rightColumn) {
      allFields = allFields.concat(flattenFields(config.rightColumn));
    }
    
    return allFields;
  }, [options.panelConfig]);

  // Filter fields that need async options
  const asyncFields = useMemo(() => {
    return fields.filter(
      field => field.type === 'select' && typeof field.options === 'function'
    ) as Array<PanelFieldConfig & { type: 'select'; options: (formData?: any) => Promise<Array<{ value: string; label: string }>> }>;
  }, [fields]);

  // Create queries for async fields
  const queries = useQueries({
    queries: asyncFields.map(field => {
      const getDependencyValues = () => {
        if (!field.dependsOn) return [];
        
        const dependencies = Array.isArray(field.dependsOn) ? field.dependsOn : [field.dependsOn];
        return dependencies.map(dep => formData[dep as keyof T]);
      };

      const checkDependencies = () => {
        if (!field.dependsOn) return true;
        
        const dependencies = Array.isArray(field.dependsOn) ? field.dependsOn : [field.dependsOn];
        return dependencies.every(dep => {
          const value = formData[dep as keyof T];
          return value !== undefined && value !== null && value !== '';
        });
      };

      return {
        queryKey: ['field-options', field.name, ...getDependencyValues()],
        queryFn: async () => {
          const optionsFn = field.options as (formData?: T) => Promise<Array<{ value: string; label: string }>>;
          
          if (field.dependsOn) {
            return await optionsFn(formData);
          }
          
          return await optionsFn();
        },
        enabled: checkDependencies(),
        staleTime: 5 * 60 * 1000,
        cacheTime: 10 * 60 * 1000,
      };
    })
  });

  // Create a map of field names to their query results
  const optionsMap = useMemo(() => {
    const map = new Map<string, ProcessedField['options']>();
    const loadingMap = new Map<string, boolean>();
    const errorMap = new Map<string, Error | null>();
    
    asyncFields.forEach((field, index) => {
      const query = queries[index];
      if (field.name && query) {
        map.set(field.name, query.data || []);
        loadingMap.set(field.name, query.isLoading);
        errorMap.set(field.name, query.error);
      }
    });
    
    return { options: map, loading: loadingMap, errors: errorMap };
  }, [asyncFields, queries]);

  // Process all fields with their options
  const processedFields = useMemo(() => {
    return fields.map(field => {
      const processed: ProcessedField = { field };
      
      if (field.type === 'select' && field.name) {
        if (typeof field.options === 'function') {
          processed.options = optionsMap.options.get(field.name) || [];
          processed.isLoading = optionsMap.loading.get(field.name) || false;
          processed.error = optionsMap.errors.get(field.name) || null;
        } else if (Array.isArray(field.options)) {
          processed.options = field.options;
        }
      }
      
      return processed;
    });
  }, [fields, optionsMap]);

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
    apiKeyOptions,
    
    // Panel schema
    processedFields,
    fields,
  };
};