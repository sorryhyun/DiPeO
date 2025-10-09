import { useMemo, useCallback, useRef, useEffect } from 'react';
import { useCanvasState, useCanvasOperations } from '@/domain/diagram';
import { arrowId, nodeId, personId } from '@/infrastructure/types';
import { TypedPanelFieldConfig, PanelLayoutConfig } from '@/domain/diagram/types/panel';
import { useFormManager } from '@/infrastructure/hooks/forms';
import { JsonDict } from '@dipeo/models';
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

  const entityIdRef = useRef(entityId);
  const initialDataRef = useRef(initialData);
  const hasEntityChanged = entityId !== entityIdRef.current;

  const hasInitialDataChanged = useMemo(() => {
    return JSON.stringify(initialData) !== JSON.stringify(initialDataRef.current);
  }, [initialData]);

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

  const handleAutoSave = useCallback(async (data: T) => {
    if (isMonitorMode) return;

    try {
      if (onSave) {
        await onSave(data);
      } else {
        if (entityType === 'node') {
          const nodeData = data as Record<string, unknown>;
          if (nodeData.type === 'person_job' && 'memory_profile' in nodeData) {
            const transformedData = { ...nodeData };
            const memoryProfile = nodeData.memory_profile as string;

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
                if (!transformedData.memory_settings) {
                  transformedData.memory_settings = {
                    view: 'all_involved',
                    max_messages: null,
                    preserve_system: true
                  };
                }
                break;
            }

            updateNode(nodeId(entityId), { data: transformedData as JsonDict });
          } else {
            updateNode(nodeId(entityId), { data: nodeData as JsonDict });
          }
        } else if (entityType === 'arrow') {
          const { content_type, label, ...restData } = data as any;
          const updates: any = { data: restData };
          if (content_type !== undefined) {
            updates.content_type = content_type;
          }
          if (label !== undefined) updates.label = label;
          updateArrow(arrowId(entityId), updates);
        } else {
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

  const autoSaveConfig: FormAutoSaveConfig | undefined = autoSave ? {
    enabled: autoSave && !isMonitorMode,
    delay: autoSaveDelay,
    onSave: handleAutoSave
  } : undefined;

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

  const formDataRef = useRef<T>(initialData);

  const asyncFieldsConfig = useMemo(() => {
    const config: Record<string, AsyncFieldOptions> = {};

    fields.forEach(field => {
      if (field.type === 'select' && typeof field.options === 'function' && field.name) {
        const dependencies = field.dependsOn
          ? (Array.isArray(field.dependsOn) ? field.dependsOn : [field.dependsOn])
          : [];

        config[field.name] = {
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

  const formConfig: FormConfig<T> = {
    initialValues: initialData,
    validators,
    validateOnChange: true,
    validateOnBlur: true,
    enableReinitialize: true
  };

  const form = useFormManager({
    config: formConfig,
    autoSave: autoSaveConfig,
    asyncFields: asyncFieldsConfig,
    onSubmit: onSave
  });

  useEffect(() => {
    formDataRef.current = form.formState.data;
  }, [form.formState.data]);

  useEffect(() => {
    if (hasEntityChanged) {
      entityIdRef.current = entityId;
      initialDataRef.current = initialData;
      form.operations.reset(initialData);
    } else if (hasInitialDataChanged && hasEntityChanged === false) {
      initialDataRef.current = initialData;
    }
  }, [entityId, hasEntityChanged, hasInitialDataChanged, form.operations, initialData]);

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

    updateField: <K extends keyof T>(field: K, value: T[K]) => {
      formDataRef.current = { ...formDataRef.current, [field]: value };
      form.operations.updateField({ field: String(field), value });
    },
    updateFormData: (updates: Partial<T>) => {
      formDataRef.current = { ...formDataRef.current, ...updates };
      form.operations.updateFields(updates);
    },
    save,
    reset: form.operations.reset,
    validateForm: form.operations.validateForm,

    processedFields,
    fields,
  };
};
