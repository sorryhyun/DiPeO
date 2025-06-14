import React, { useCallback } from 'react';
import { PanelConfig, PanelFieldConfig } from '@/types';
import { usePropertyManager } from '@/hooks/usePropertyManager';
import { useCanvasOperations } from '@/hooks';
import { UnifiedFormField, type FieldValue } from '../fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from '../fields/FormComponents';
import { preInitializeModel, fetchApiKeys } from '@/utils/api';
import { createHandlerTable } from '@/utils/dispatchTable';

interface GenericPropertyPanelProps<T extends Record<string, unknown>> {
  nodeId: string;
  data: T;
  config: PanelConfig<T>;
}

// Create dispatch tables for operators and field types
const conditionalOperators = createHandlerTable<string, [unknown, unknown[]], boolean>({
  'equals': (fieldValue, values) => values.includes(fieldValue),
  'notEquals': (fieldValue, values) => !values.includes(fieldValue),
  'includes': (fieldValue, values) => values.includes(fieldValue)
}, (fieldValue, values) => values.includes(fieldValue)); // Default to 'includes'

const fieldTypeMapping = createHandlerTable<string, [], string>({
  'text': () => 'text',
  'select': () => 'select',
  'textarea': () => 'textarea',
  'variableTextArea': () => 'variable-textarea',
  'checkbox': () => 'checkbox',
  'maxIteration': () => 'iteration-count',
  'personSelect': () => 'person-select'
}, () => 'text'); // Default to 'text'

export const GenericPropertyPanel = <T extends Record<string, unknown>>({
  nodeId,
  data,
  config
}: GenericPropertyPanelProps<T>) => {

  const canvas = useCanvasOperations();

  // Convert persons to the format expected by UnifiedFormField
  const persons = canvas.persons.map(id => canvas.getPersonById(id)).filter(Boolean);
  const personsForSelect = persons.map(person => ({ id: person.id, label: person.label }));
  
  // Determine entity type based on data.type
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);

  // Use enhanced property manager with panel schema support
  // Use minimal delay for all entities to provide immediate feedback
  const {
    formData,
    updateField,
    processedFields,
    isReadOnly
  } = usePropertyManager<T>(nodeId, entityType, data, {
    autoSave: true,
    autoSaveDelay: 50,
    panelConfig: config
  });

  // Handle field updates with model pre-initialization
  const handleFieldUpdate = useCallback(async (name: string, value: unknown) => {
    // Update field using property manager
    updateField(name as keyof T, value as T[keyof T]);
    
    // If this is an API key selection for a person entity, update the service field
    if (data.type === 'person' && name === 'apiKeyId' && value) {
      try {
        const apiKeys = await fetchApiKeys();
        const selectedKey = apiKeys.find(k => k.id === value);
        if (selectedKey) {
          updateField('service' as keyof T, selectedKey.service as T[keyof T]);
        }
      } catch (error) {
        console.error('Failed to update service:', error);
      }
    }
    
    // If this is a model selection for a person entity, pre-initialize the model
    if (data.type === 'person' && name === 'model') {
      const service = formData.service || data.service;
      const apiKeyId = formData.apiKeyId || data.apiKeyId;
      
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
  }, [updateField, formData, data]);

  // Check if field should be rendered based on conditional rules
  const shouldRenderField = useCallback((fieldConfig: PanelFieldConfig): boolean => {
    if (!fieldConfig.conditional) return true;
    
    const fieldValue = formData[fieldConfig.conditional.field];
    const { values, operator = 'includes' } = fieldConfig.conditional;
    
    return conditionalOperators.executeOrDefault(operator, fieldValue, values);
  }, [formData]);

  // Convert field type to UnifiedFormField type
  const getFieldType = (fieldConfig: PanelFieldConfig): "number" | "text" | "select" | "textarea" | "variable-textarea" | "checkbox" | "iteration-count" | "person-select" | "file" => {
    return fieldTypeMapping.executeOrDefault(fieldConfig.type) as any;
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
            value={formData.label as FieldValue}
            onChange={(v) => handleFieldUpdate('label', v)}
            placeholder={fieldConfig.labelPlaceholder}
            disabled={isReadOnly}
          />
          <UnifiedFormField
            type="person-select"
            name="personId"
            label="Person"
            value={formData.personId as FieldValue}
            onChange={(v) => handleFieldUpdate('personId', v)}
            placeholder={fieldConfig.personPlaceholder}
            disabled={isReadOnly}
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
    
    const fieldValue = fieldConfig.name ? formData[fieldConfig.name] : undefined;
    
    return (
      <UnifiedFormField
        key={key}
        type={getFieldType(fieldConfig)}
        name={fieldConfig.name || ''}
        label={fieldConfig.label || ''}
        value={fieldValue as FieldValue}
        onChange={(v) => handleFieldUpdate(fieldConfig.name || '', v)}
        placeholder={'placeholder' in fieldConfig ? fieldConfig.placeholder : undefined}
        options={fieldConfig.type === 'select' ? options : undefined}
        disabled={isReadOnly || ('disabled' in fieldConfig && fieldConfig.disabled) || isLoading}
        required={false}
        min={fieldConfig.type === 'maxIteration' ? fieldConfig.min : undefined}
        max={fieldConfig.type === 'maxIteration' ? fieldConfig.max : undefined}
        helperText={undefined}
        acceptedFileTypes={undefined}
        detectedVariables={formData.detectedVariables as string[] | undefined}
        className={fieldConfig.className}
        rows={fieldConfig.type === 'textarea' || fieldConfig.type === 'variableTextArea' ? fieldConfig.rows : undefined}
        persons={getFieldType(fieldConfig) === 'person-select' ? personsForSelect : undefined}
      />
    );
  }, [formData, handleFieldUpdate, isReadOnly, personsForSelect, shouldRenderField, processedFields]);

  const renderSection = useCallback((fields: PanelFieldConfig[] | undefined) => {
    if (!fields) {
      return null;
    }
    return fields.map((field, index) => renderField(field, index));
  }, [renderField]);

  return (
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
  );
};