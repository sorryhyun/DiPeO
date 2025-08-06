import { useMemo, useCallback, useRef, useEffect } from 'react';
import { useCanvasState, useCanvasOperations } from '@/domain/diagram';
import { arrowId, nodeId, personId } from '@/infrastructure/types';
import { TypedPanelFieldConfig, PanelLayoutConfig } from '@/domain/diagram/types/panel';
import { useFormManager } from '@/infrastructure/hooks/forms';
import type {
  FormConfig, 
  FormAutoSaveConfig,
  FieldValidator,
  AsyncFieldOptions
} from '@/domain/diagram/forms/types';

interface ValidationRule<T extends Record<string, unknown> = Record<string, unknown>> {
  field: keyof T;
  validator: (value: unknown, formData: T) => string | null;
}

interface ProcessedField<T extends Record<string, unknown> = Record<string, unknown>> {
  field: TypedPanelFieldConfig<T>;
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
  panelConfig?: PanelLayoutConfig<T>;
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
    onError,
    panelConfig
  } = options;

  // Get operations from context
  const { readOnly } = useCanvasState();
  const { nodeOps, arrowOps, personOps } = useCanvasOperations();
  const { updateNode } = nodeOps;
  const { updateArrow } = arrowOps;
  const { updatePerson } = personOps;
  const isMonitorMode = readOnly;

  // Track entity ID changes and initial data
  const entityIdRef = useRef(entityId);
  const initialDataRef = useRef(initialData);
  const hasEntityChanged = entityId !== entityIdRef.current;
  
  // Deep compare initial data to prevent unnecessary resets
  const hasInitialDataChanged = useMemo(() => {
    return JSON.stringify(initialData) !== JSON.stringify(initialDataRef.current);
  }, [initialData]);

  // Convert validation rules to field validators
  const validators = useMemo(() => {
    const fieldValidators: Record<string, FieldValidator> = {};
    
    validationRules.forEach(rule => {
      fieldValidators[String(rule.field)] = (value, formData) => {
        const error = rule.validator(value, formData as T);
        return {
          valid: !error,
          errors: error ? [{ field: String(rule.field), message: error }] : []
        };
      };
    });
    
    return fieldValidators;
  }, [validationRules]);

  // Auto-save handler
  const handleAutoSave = useCallback(async (data: T) => {
    if (isMonitorMode) return;
    
    try {
      if (onSave) {
        await onSave(data);
      } else {
        // Store update logic
        if (entityType === 'node') {
          // Transform memory_profile to memory_settings for person_job nodes
          const nodeData = data as Record<string, unknown>;
          if (nodeData.type === 'person_job' && 'memory_profile' in nodeData) {
            const transformedData = { ...nodeData };
            const memoryProfile = nodeData.memory_profile as string;
            
            // Map memory profile to memory settings
            switch (memoryProfile) {
              case 'FULL':
                transformedData.memory_settings = {
                  view: 'all_messages',
                  max_messages: null,
                  preserve_system: true
                };
                break;
              case 'FOCUSED':
                transformedData.memory_settings = {
                  view: 'conversation_pairs',
                  max_messages: 20,
                  preserve_system: true
                };
                break;
              case 'MINIMAL':
                transformedData.memory_settings = {
                  view: 'system_and_me',
                  max_messages: 5,
                  preserve_system: true
                };
                break;
              case 'GOLDFISH':
                transformedData.memory_settings = {
                  view: 'conversation_pairs',
                  max_messages: 1,
                  preserve_system: false
                };
                break;
              case 'CUSTOM':
                // Keep existing memory_settings or use defaults
                if (!transformedData.memory_settings) {
                  transformedData.memory_settings = {
                    view: 'all_involved',
                    max_messages: null,
                    preserve_system: true
                  };
                }
                break;
            }
            
            // Don't remove memory_profile - it's a UI field that needs to be preserved
            // The domain model will ignore it, but we need it for the UI
            
            updateNode(nodeId(entityId), { data: transformedData });
          } else {
            updateNode(nodeId(entityId), { data: nodeData });
          }
        } else if (entityType === 'arrow') {
          const { content_type, label, ...restData } = data as any;
          const updates: any = { data: restData };
          if (content_type !== undefined) {
            // Keep content_type as lowercase for backend compatibility
            updates.content_type = content_type;
          }
          if (label !== undefined) updates.label = label;
          updateArrow(arrowId(entityId), updates);
        } else {
          // Person entity flattening logic
          const unflattenedData: any = {};
          const llmConfig: any = {};
          
          Object.entries(data).forEach(([key, value]) => {
            if (key.startsWith('llm_config.')) {
              const fieldName = key.substring('llm_config.'.length);
              llmConfig[fieldName] = value;
            } else {
              unflattenedData[key] = value;
            }
          });
          
          if (Object.keys(llmConfig).length > 0) {
            unflattenedData.llm_config = llmConfig;
          }
          
          updatePerson(personId(entityId), unflattenedData);
        }
      }
    } catch (error) {
      if (onError) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to auto-save';
        onError(errorMessage);
      }
      throw error;
    }
  }, [entityId, entityType, isMonitorMode, onSave, updateNode, updateArrow, updatePerson, onError]);

  // Auto-save configuration
  const autoSaveConfig: FormAutoSaveConfig | undefined = autoSave ? {
    enabled: autoSave && !isMonitorMode,
    delay: autoSaveDelay,
    onSave: handleAutoSave
  } : undefined;

  // Process panel fields
  const fields = useMemo(() => {
    if (!panelConfig) return [];
    
    const flattenFields = (fields: TypedPanelFieldConfig<T>[]): TypedPanelFieldConfig<T>[] => {
      const result: TypedPanelFieldConfig<T>[] = [];
      
      fields.forEach(field => {
        if (field.type === 'row' && field.fields) {
          result.push(...flattenFields(field.fields));
        } else {
          result.push(field);
        }
      });
      
      return result;
    };
    
    let allFields: TypedPanelFieldConfig<T>[] = [];
    
    if (panelConfig.fields) {
      allFields = allFields.concat(flattenFields(panelConfig.fields));
    }
    if (panelConfig.leftColumn) {
      allFields = allFields.concat(flattenFields(panelConfig.leftColumn));
    }
    if (panelConfig.rightColumn) {
      allFields = allFields.concat(flattenFields(panelConfig.rightColumn));
    }
    
    return allFields;
  }, [panelConfig]);
  
  // Store a ref to current form data for async field options
  const formDataRef = useRef<T>(initialData);
  
  // Extract async fields configuration with stable references
  const asyncFieldsConfig = useMemo(() => {
    const config: Record<string, AsyncFieldOptions> = {};
    
    fields.forEach(field => {
      if (field.type === 'select' && typeof field.options === 'function' && field.name) {
        const dependencies = field.dependsOn 
          ? (Array.isArray(field.dependsOn) ? field.dependsOn : [field.dependsOn])
          : [];
          
        config[field.name] = {
          // Use a more specific query key to avoid conflicts
          queryKey: ['field-options', entityType, entityId, field.name],
          queryFn: async () => {
            const optionsFn = field.options as (formData?: T) => Promise<Array<{ value: string; label: string }>>;
            return field.dependsOn ? await optionsFn(formDataRef.current) : await optionsFn();
          },
          dependencies: dependencies as string[],
          enabled: true
        };
      }
    });
    
    return config;
  }, [fields, entityType, entityId]);

  // Form configuration
  const formConfig: FormConfig<T> = {
    initialValues: initialData,
    validators,
    validateOnChange: true,
    validateOnBlur: true,
    enableReinitialize: true
  };

  // Use the form manager
  const form = useFormManager({
    config: formConfig,
    autoSave: autoSaveConfig,
    asyncFields: asyncFieldsConfig,
    onSubmit: onSave
  });
  
  // Keep formDataRef updated
  useEffect(() => {
    formDataRef.current = form.formState.data;
  }, [form.formState.data]);

  // Handle entity changes
  useEffect(() => {
    if (hasEntityChanged) {
      entityIdRef.current = entityId;
      initialDataRef.current = initialData;
      form.operations.reset(initialData);
    } else if (hasInitialDataChanged && hasEntityChanged === false) {
      // Only update the ref, don't reset the form for data changes on the same entity
      initialDataRef.current = initialData;
    }
  }, [entityId, hasEntityChanged, hasInitialDataChanged, form.operations, initialData]);

  // Process fields with their async options
  const processedFields = useMemo(() => {
    return fields.map(field => {
      const processed: ProcessedField<T> = { field };
      
      if (field.type === 'select' && field.name) {
        if (typeof field.options === 'function') {
          const query = form.asyncFields.queries[field.name];
          if (query) {
            processed.options = (query.data as Array<{ value: string; label: string }>) || [];
            processed.isLoading = query.isLoading;
            processed.error = query.error;
          }
        } else if (Array.isArray(field.options)) {
          processed.options = field.options;
        }
      }
      
      return processed;
    });
  }, [fields, form.asyncFields.queries]);

  // Handle form submission
  const save = useCallback(async () => {
    try {
      await form.handlers.handleSubmit();
      return true;
    } catch (error) {
      if (onError) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to save';
        onError(errorMessage);
      }
      return false;
    }
  }, [form.handlers, onError]);

  return {
    // Form data
    formData: form.formState.data,
    isDirty: form.computed.isDirty,
    errors: Object.fromEntries(
      Object.entries(form.formState.errors).map(([field, errors]) => [
        field,
        errors[0]?.message || ''
      ])
    ),
    isSubmitting: form.formState.isSubmitting,
    lastSaved: form.autoSave?.lastSaved || null,
    hasErrors: form.computed.hasErrors,
    isReadOnly: isMonitorMode,
    
    // Actions
    updateField: <K extends keyof T>(field: K, value: T[K]) => {
      // Update ref immediately for async field dependencies
      formDataRef.current = { ...formDataRef.current, [field]: value };
      form.operations.updateField({ field: String(field), value });
    },
    updateFormData: (updates: Partial<T>) => {
      // Update ref immediately for async field dependencies
      formDataRef.current = { ...formDataRef.current, ...updates };
      form.operations.updateFields(updates);
    },
    save,
    reset: form.operations.reset,
    validateForm: form.operations.validateForm,
    
    // Panel schema
    processedFields,
    fields,
  };
};