import React, { useCallback } from 'react';
import { PanelConfig, PanelFieldConfig } from '@/features/diagram-editor/types/panel';
import { FIELD_TYPES } from '@/core/types/panel';
import { usePropertyManager } from '../../hooks';
import { usePersonsData } from '@/shared/hooks/selectors';
import { UnifiedFormField, type FieldValue, type UnifiedFieldType } from '../fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from '../fields/FormComponents';
import { apolloClient } from '@/graphql/client';
import { GetApiKeysDocument, InitializeModelDocument } from '@/__generated__/graphql';
import { createHandlerTable } from '@/shared/utils/dispatchTable';

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

const fieldTypeMapping = createHandlerTable<string, [], UnifiedFieldType>({
  'text': () => FIELD_TYPES.TEXT,
  'select': () => FIELD_TYPES.SELECT,
  'textarea': () => FIELD_TYPES.TEXTAREA,
  'variableTextArea': () => FIELD_TYPES.VARIABLE_TEXTAREA,
  'checkbox': () => FIELD_TYPES.BOOLEAN,
  'maxIteration': () => FIELD_TYPES.MAX_ITERATION,
  'personSelect': () => FIELD_TYPES.PERSON_SELECT
}, () => FIELD_TYPES.TEXT); // Default to 'text'

export const GenericPropertyPanel = <T extends Record<string, unknown>>({
  nodeId,
  data,
  config
}: GenericPropertyPanelProps<T>) => {

  const { personsArray } = usePersonsData();

  // Convert persons to the format expected by UnifiedFormField
  const personsForSelect = personsArray.map(person => ({ id: person.id, label: person.label }));
  
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
        const { data } = await apolloClient.query({
          query: GetApiKeysDocument,
          fetchPolicy: 'cache-first'
        });
        const selectedKey = data.apiKeys.find((k: any) => k.id === value);
        if (selectedKey) {
          updateField('service' as keyof T, selectedKey.service as T[keyof T]);
        }
      } catch (error) {
        console.error('Failed to update service:', error);
      }
    }
    
    // If this is a model selection for a person entity, pre-initialize the model
    if (data.type === 'person' && name === 'model' && value) {
      try {
        const personId = nodeId; // For person entities, nodeId is the person ID
        const { data: result } = await apolloClient.mutate({
          mutation: InitializeModelDocument,
          variables: { personId }
        });
        
        if (!result?.initializeModel?.success) {
          console.error('Failed to initialize model:', result?.initializeModel?.error);
        }
      } catch (error) {
        console.error('Error initializing model:', error);
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
  const getFieldType = (fieldConfig: PanelFieldConfig): UnifiedFieldType => {
    return fieldTypeMapping.executeOrDefault(fieldConfig.type);
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
            type="personSelect"
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
        persons={getFieldType(fieldConfig) === FIELD_TYPES.PERSON_SELECT ? personsForSelect : undefined}
        showFieldKey={false}
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