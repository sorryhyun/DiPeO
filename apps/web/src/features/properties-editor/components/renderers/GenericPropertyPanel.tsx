import React, { useCallback } from 'react';
import { TypedPanelFieldConfig, PanelLayoutConfig } from '@/features/diagram-editor/types/panel';
import { FIELD_TYPES } from '@/core/types/panel';
import { usePropertyManager } from '../../hooks';
import { usePersonsData } from '@/shared/hooks/selectors';
import { UnifiedFormField, type FieldValue, type UnifiedFieldType } from '../fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from '../fields/FormComponents';
import { apolloClient } from '@/graphql/client';
import { GetApiKeysDocument, InitializeModelDocument, type GetApiKeysQuery } from '@/__generated__/graphql';
import { createHandlerTable } from '@/shared/utils/dispatchTable';

interface GenericPropertyPanelProps<T extends Record<string, unknown>> {
  nodeId: string;
  data: T;
  config: PanelLayoutConfig<T>;
}

const conditionalOperators = createHandlerTable<string, [unknown, unknown[]], boolean>({
  'equals': (fieldValue, values) => values.includes(fieldValue),
  'notEquals': (fieldValue, values) => !values.includes(fieldValue),
  'includes': (fieldValue, values) => values.includes(fieldValue)
}, (fieldValue, values) => values.includes(fieldValue));

const fieldTypeMapping = createHandlerTable<string, [], UnifiedFieldType>({
  'text': () => FIELD_TYPES.TEXT,
  'select': () => FIELD_TYPES.SELECT,
  'textarea': () => FIELD_TYPES.TEXTAREA,
  'variableTextArea': () => FIELD_TYPES.VARIABLE_TEXTAREA,
  'checkbox': () => FIELD_TYPES.BOOLEAN,
  'max_iteration': () => FIELD_TYPES.MAX_ITERATION,
  'personSelect': () => FIELD_TYPES.PERSON_SELECT
}, () => FIELD_TYPES.TEXT);

// Helper function to flatten nested object properties
function flattenObject(obj: Record<string, unknown>, prefix = ''): Record<string, unknown> {
  const flattened: Record<string, unknown> = {};
  
  Object.keys(obj).forEach(key => {
    const value = obj[key];
    const newKey = prefix ? `${prefix}.${key}` : key;
    
    if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      Object.assign(flattened, flattenObject(value as Record<string, unknown>, newKey));
    } else {
      flattened[newKey] = value;
    }
  });
  
  return flattened;
}

export const GenericPropertyPanel = <T extends Record<string, unknown>>({
  nodeId,
  data,
  config
}: GenericPropertyPanelProps<T>) => {

  const { personsArray } = usePersonsData();

  const personsForSelect = personsArray.map(person => ({ id: person.id, label: person.label }));
  
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);

  // Flatten the data for form fields if it's a person
  const flattenedData = entityType === 'person' ? flattenObject(data) : data;

  const {
    formData,
    updateField,
    processedFields,
    isReadOnly
  } = usePropertyManager<T>(nodeId, entityType, flattenedData as T, {
    autoSave: true,
    autoSaveDelay: 50,
    panelConfig: config
  });

  const handleFieldUpdate = useCallback(async (name: string, value: unknown) => {
    updateField(name as keyof T, value as T[keyof T]);
    
    if (data.type === 'person' && name === 'llm_config.api_key_id' && value) {
      try {
        const { data } = await apolloClient.query<GetApiKeysQuery>({
          query: GetApiKeysDocument,
          fetchPolicy: 'cache-first'
        });
        const selectedKey = data.api_keys.find((k) => k.id === value);
        if (selectedKey) {
          updateField('llm_config.service' as keyof T, selectedKey.service as T[keyof T]);
        }
      } catch (error) {
        console.error('Failed to update service:', error);
      }
    }
    
    if (data.type === 'person' && name === 'llm_config.model' && value) {
      try {
        const personId = nodeId;
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

  const shouldRenderField = useCallback((fieldConfig: TypedPanelFieldConfig<T>): boolean => {
    if (!fieldConfig.conditional) return true;
    
    const fieldValue = formData[fieldConfig.conditional.field];
    const { values, operator = 'includes' } = fieldConfig.conditional;
    
    return conditionalOperators.executeOrDefault(operator, fieldValue, values);
  }, [formData]);

  const getFieldType = (fieldConfig: TypedPanelFieldConfig<T>): UnifiedFieldType => {
    return fieldTypeMapping.executeOrDefault(fieldConfig.type);
  };

  const renderField = useCallback((fieldConfig: TypedPanelFieldConfig<T>, index: number): React.ReactNode => {
    const key = fieldConfig.name ? `${fieldConfig.name}-${index}` : `field-${index}`;
    
    if (!shouldRenderField(fieldConfig)) return null;
    
    if (fieldConfig.type === 'row' && fieldConfig.fields) {
      return (
        <FormRow key={key} className={fieldConfig.className}>
          {fieldConfig.fields.map((field, idx) => renderField(field, idx))}
        </FormRow>
      );
    }
    
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
            name="person"
            label="Person"
            value={formData.person as FieldValue}
            onChange={(v) => handleFieldUpdate('person', v)}
            placeholder={fieldConfig.personPlaceholder}
            disabled={isReadOnly}
            persons={personsForSelect}
          />
        </FormRow>
      );
    }
    
    if (fieldConfig.type === 'custom') return null;
    
    const processedField = processedFields.find((pf: { field: { name?: string } }) => pf.field.name === fieldConfig.name);
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
        disabled={isReadOnly || (fieldConfig.disabled ? (typeof fieldConfig.disabled === 'function' ? fieldConfig.disabled(formData) : fieldConfig.disabled) : false) || isLoading}
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
  }, [formData, handleFieldUpdate, isReadOnly, personsForSelect, shouldRenderField, processedFields, getFieldType]);

  const renderSection = useCallback((fields: TypedPanelFieldConfig<T>[] | undefined) => {
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