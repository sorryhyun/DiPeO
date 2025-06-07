import React, { useEffect, useCallback } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PanelConfig, PanelFieldConfig, Person } from '@/types';
import { usePanelSchema } from '@/hooks/usePanelSchema';
import { useIsReadOnly, usePersons } from '@/hooks/useStoreSelectors';
import { UnifiedFormField } from '../fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from '../fields/FormComponents';
import { preInitializeModel } from '@/utils/api';
import { useDiagramStore } from '@/stores/diagramStore';

interface GenericPropertyPanelProps<T extends Record<string, unknown>> {
  nodeId: string;
  data: T;
  config: PanelConfig<T>;
}

export const GenericPropertyPanel = <T extends Record<string, unknown>>({
  nodeId,
  data,
  config
}: GenericPropertyPanelProps<T>) => {
  const queryClient = useQueryClient();
  const isMonitorMode = useIsReadOnly();
  const { persons } = usePersons();

  // Convert persons to the format expected by UnifiedFormField
  const personsForSelect = persons.map(person => ({ id: person.id, name: person.label }));
  
  // Determine entity type based on data.type
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);

  // Initialize React Hook Form
  const form = useForm<T>({
    defaultValues: data as any,
    mode: 'onChange',
  });

  // Get processed fields with async options
  const processedFields = usePanelSchema(config, form);

  // Get store actions
  const { updateNode, updateArrow, updatePerson } = useDiagramStore();

  // Create mutation for saving data
  const saveMutation = useMutation({
    mutationFn: async (values: T) => {
      // Save to the appropriate store based on entity type
      if (entityType === 'node') {
        updateNode(nodeId, values);
      } else if (entityType === 'arrow') {
        updateArrow(nodeId, values);
      } else if (entityType === 'person') {
        updatePerson(nodeId, values as Partial<Person>);
      }
      
      return values;
    },
    onSuccess: () => {
      // Invalidate relevant queries if needed
      queryClient.invalidateQueries({ queryKey: ['diagram'] });
    },
  });

  // Auto-save on form changes with debounce
  useEffect(() => {
    if (isMonitorMode) return;
    
    let timeoutId: ReturnType<typeof setTimeout>;
    
    const subscription = form.watch((value) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        saveMutation.mutate(value as T);
      }, 500); // 500ms debounce
    });
    
    return () => {
      clearTimeout(timeoutId);
      subscription.unsubscribe();
    };
  }, [form, saveMutation, isMonitorMode]);

  // Handle field updates with model pre-initialization
  const updateField = useCallback(async (name: string, value: unknown) => {
    if (isMonitorMode) return;
    
    // Update form value
    form.setValue(name as any, value as any, { shouldDirty: true });
    
    // If this is a model selection for a person entity, pre-initialize the model
    if (data.type === 'person' && name === 'modelName') {
      const formValues = form.getValues();
      const service = formValues.service || data.service;
      const apiKeyId = formValues.apiKeyId || data.apiKeyId;
      
      if (service && value && apiKeyId) {
        try {
          await preInitializeModel(
            service as string,
            value as string,
            apiKeyId as string
          );
        } catch (error) {
          console.warn('Failed to pre-initialize model:', error);
        }
      }
    }
  }, [isMonitorMode, form, data]);

  // Check if field should be rendered based on conditional rules
  const shouldRenderField = useCallback((fieldConfig: PanelFieldConfig): boolean => {
    if (!fieldConfig.conditional) return true;
    
    const formData = form.watch();
    const fieldValue = formData[fieldConfig.conditional.field];
    const { values, operator = 'includes' } = fieldConfig.conditional;
    
    switch (operator) {
      case 'equals':
        return values.includes(fieldValue);
      case 'notEquals':
        return !values.includes(fieldValue);
      case 'includes':
      default:
        return values.includes(fieldValue);
    }
  }, [form]);

  // Convert field type to UnifiedFormField type
  const getFieldType = (fieldConfig: PanelFieldConfig) => {
    switch (fieldConfig.type) {
      case 'text':
        return 'text';
      case 'select':
        return 'select';
      case 'textarea':
        return 'textarea';
      case 'variableTextArea':
        return 'variable-textarea';
      case 'checkbox':
        return 'checkbox';
      case 'maxIteration':
        return 'iteration-count';
      case 'personSelect':
        return 'person-select';
      default:
        return 'text';
    }
  };

  // Render individual field
  const renderField = useCallback((fieldConfig: PanelFieldConfig, index: number): React.ReactNode => {
    const key = fieldConfig.name ? `${fieldConfig.name}-${index}` : `field-${index}`;
    
    // Check conditional rendering
    if (!shouldRenderField(fieldConfig)) return null;
    
    // Handle special row type
    if (fieldConfig.type === 'row' && fieldConfig.fields) {
      return (
        <FormRow key={key} className={fieldConfig.className}>
          {fieldConfig.fields.map((field, idx) => renderField(field, idx))}
        </FormRow>
      );
    }
    
    // Handle labelPersonRow type
    if (fieldConfig.type === 'labelPersonRow') {
      return (
        <FormRow key={key}>
          <UnifiedFormField
            type="text"
            name="label"
            label="Label"
            value={form.watch('label' as any)}
            onChange={(v) => updateField('label', v)}
            placeholder={fieldConfig.labelPlaceholder}
            disabled={isMonitorMode}
          />
          <UnifiedFormField
            type="person-select"
            name="personId"
            label="Person"
            value={form.watch('personId' as any)}
            onChange={(v) => updateField('personId', v)}
            placeholder={fieldConfig.personPlaceholder}
            disabled={isMonitorMode}
            persons={personsForSelect}
          />
        </FormRow>
      );
    }
    
    // Skip non-standard field types
    if (fieldConfig.type === 'custom') return null;
    
    // Find the processed field data
    const processedField = processedFields.find(pf => pf.field.name === fieldConfig.name);
    const options = processedField?.options;
    const isLoading = processedField?.isLoading;
    
    const fieldValue = fieldConfig.name ? form.watch(fieldConfig.name as any) : undefined;
    
    return (
      <UnifiedFormField
        key={key}
        type={getFieldType(fieldConfig)}
        name={fieldConfig.name || ''}
        label={fieldConfig.label || ''}
        value={fieldValue}
        onChange={(v) => updateField(fieldConfig.name || '', v)}
        placeholder={'placeholder' in fieldConfig ? fieldConfig.placeholder : undefined}
        options={fieldConfig.type === 'select' ? options : undefined}
        disabled={isMonitorMode || ('disabled' in fieldConfig && fieldConfig.disabled) || isLoading}
        required={'isRequired' in fieldConfig ? (fieldConfig as any).isRequired : undefined}
        min={fieldConfig.type === 'maxIteration' ? fieldConfig.min : undefined}
        max={fieldConfig.type === 'maxIteration' ? fieldConfig.max : undefined}
        helperText={'helperText' in fieldConfig ? (fieldConfig as any).helperText : undefined}
        acceptedFileTypes={'acceptedFileTypes' in fieldConfig ? (fieldConfig as any).acceptedFileTypes : undefined}
        detectedVariables={form.watch('detectedVariables' as any) as string[] | undefined}
        className={fieldConfig.className}
        rows={fieldConfig.type === 'textarea' || fieldConfig.type === 'variableTextArea' ? fieldConfig.rows : undefined}
        persons={getFieldType(fieldConfig) === 'person-select' ? personsForSelect : undefined}
      />
    );
  }, [form, updateField, isMonitorMode, personsForSelect, shouldRenderField, processedFields]);

  const renderSection = useCallback((fields: PanelFieldConfig[] | undefined) => {
    if (!fields) return null;
    return fields.map((field, index) => renderField(field, index));
  }, [renderField]);

  return (
    <FormProvider {...form}>
      <Form>
        {config.layout === 'twoColumn' ? (
          <TwoColumnPanelLayout
            leftColumn={renderSection(config.leftColumn)}
            rightColumn={renderSection(config.rightColumn)}
          />
        ) : config.layout === 'single' ? (
          <SingleColumnPanelLayout>
            {renderSection(config.fields)}
          </SingleColumnPanelLayout>
        ) : (
          renderSection(config.fields)
        )}
      </Form>
    </FormProvider>
  );
};