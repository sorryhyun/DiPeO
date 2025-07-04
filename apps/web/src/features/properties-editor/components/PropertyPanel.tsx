import React, { useCallback } from 'react';
import { Settings, Trash2 } from 'lucide-react';
import { ArrowData, Dict, DomainPerson, nodeId, arrowId, personId } from '@/core/types';
import { PanelLayoutConfig, TypedPanelFieldConfig } from '@/features/diagram-editor/types/panel';
import { NodeType } from '@dipeo/domain-models';
import { UNIFIED_NODE_CONFIGS, getPanelConfig } from '@/core/config';
import { FIELD_TYPES } from '@/core/types/panel';
import { useCanvasOperationsContext, useCanvasPersons } from '@/features/diagram-editor';
import { usePropertyManager } from '../hooks';
import { UnifiedFormField, type FieldValue, type UnifiedFieldType } from './fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from './fields/FormComponents';
import { apolloClient } from '@/graphql/client';
import { GetApiKeysDocument, InitializeModelDocument, type GetApiKeysQuery } from '@/__generated__/graphql';

// Union type for all possible data types
type NodeData = Dict & { type: string };
export type UniversalData = NodeData | (ArrowData & { type: 'arrow' }) | (DomainPerson & { type: 'person' });

interface PropertyPanelProps {
  entityId: string;
  data: UniversalData;
}

// Simple conditional operators
function checkCondition(operator: string, fieldValue: unknown, values: unknown[]): boolean {
  switch (operator) {
    case 'equals':
    case 'includes':
      return values.includes(fieldValue);
    case 'notEquals':
      return !values.includes(fieldValue);
    default:
      return values.includes(fieldValue);
  }
}

// Simple field type mapping
function getFieldType(type: string): UnifiedFieldType {
  switch (type) {
    case 'text': return FIELD_TYPES.TEXT;
    case 'select': return FIELD_TYPES.SELECT;
    case 'textarea': return FIELD_TYPES.TEXTAREA;
    case 'variableTextArea': return FIELD_TYPES.VARIABLE_TEXTAREA;
    case 'checkbox': return FIELD_TYPES.BOOLEAN;
    case 'max_iteration': return FIELD_TYPES.MAX_ITERATION;
    case 'personSelect': return FIELD_TYPES.PERSON_SELECT;
    default: return FIELD_TYPES.TEXT;
  }
}

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

// Helper function to ensure all expected fields are present in flattened person data
function ensurePersonFields(flattenedData: Record<string, unknown>): Record<string, unknown> {
  // Ensure llm_config fields are present even if undefined
  const ensuredData = { ...flattenedData };
  
  // List of expected fields that should always be present
  const expectedFields = [
    'llm_config.api_key_id',
    'llm_config.model',
    'llm_config.service',
    'llm_config.system_prompt',
    'temperature'
  ];
  
  expectedFields.forEach(field => {
    if (!(field in ensuredData)) {
      ensuredData[field] = undefined;
    }
  });
  
  return ensuredData;
}

export const PropertyPanel: React.FC<PropertyPanelProps> = React.memo(({ entityId, data }) => {
  const nodeType = data.type;
  const nodeConfig = nodeType in UNIFIED_NODE_CONFIGS ? UNIFIED_NODE_CONFIGS[nodeType as keyof typeof UNIFIED_NODE_CONFIGS] : undefined;
  
  // Use context instead of individual hooks
  const { nodeOps, arrowOps, personOps, clearSelection } = useCanvasOperationsContext();
  const personsArray = useCanvasPersons();
  
  const panelConfig = getPanelConfig(nodeType as NodeType | 'arrow' | 'person');
  
  const personsForSelect = personsArray.map(person => ({ id: person.id, label: person.label }));
  
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);

  // Flatten the data for form fields if it's a person
  const flattenedData = entityType === 'person' ? ensurePersonFields(flattenObject(data)) : data;

  const {
    formData,
    updateField,
    processedFields,
    isReadOnly
  } = usePropertyManager(entityId, entityType, flattenedData as Record<string, unknown>, {
    autoSave: true,
    autoSaveDelay: 50,
    panelConfig: panelConfig as PanelLayoutConfig<Record<string, unknown>>
  });

  const handleFieldUpdate = useCallback(async (name: string, value: unknown) => {
    updateField(name, value);
    
    if (data.type === 'person' && name === 'llm_config.api_key_id') {
      // Clear the model when API key changes
      updateField('llm_config.model', undefined);
      
      if (value) {
        try {
          const { data } = await apolloClient.query<GetApiKeysQuery>({
            query: GetApiKeysDocument,
            fetchPolicy: 'cache-first'
          });
          const selectedKey = data.api_keys.find((k) => k.id === value);
          if (selectedKey) {
            updateField('llm_config.service', selectedKey.service);
          }
        } catch (error) {
          console.error('Failed to update service:', error);
        }
      }
    }
    
    if (data.type === 'person' && name === 'llm_config.model' && value) {
      try {
        const personId = entityId;
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
  }, [updateField, formData, data, entityId]);

  const shouldRenderField = useCallback((fieldConfig: TypedPanelFieldConfig<Record<string, unknown>>): boolean => {
    if (!fieldConfig.conditional) return true;
    
    const fieldValue = formData[fieldConfig.conditional.field];
    const { values, operator = 'includes' } = fieldConfig.conditional;
    
    return checkCondition(operator, fieldValue, values);
  }, [formData]);

  const getUnifiedFieldType = (fieldConfig: TypedPanelFieldConfig<Record<string, unknown>>): UnifiedFieldType => {
    return getFieldType(fieldConfig.type);
  };

  const renderField = useCallback((fieldConfig: TypedPanelFieldConfig<Record<string, unknown>>, index: number): React.ReactNode => {
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
        type={getUnifiedFieldType(fieldConfig)}
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
        persons={getUnifiedFieldType(fieldConfig) === FIELD_TYPES.PERSON_SELECT ? personsForSelect : undefined}
        showFieldKey={false}
        showPromptFileButton={fieldConfig.showPromptFileButton}
      />
    );
  }, [formData, handleFieldUpdate, isReadOnly, personsForSelect, shouldRenderField, processedFields]);

  const renderSection = useCallback((fields: TypedPanelFieldConfig<Record<string, unknown>>[] | undefined) => {
    if (!fields) {
      return null;
    }
    return fields.map((field, index) => renderField(field, index));
  }, [renderField]);

  const handleDelete = () => {
    if (data.type === 'person') {
      personOps.deletePerson(personId(entityId));
    } else if (data.type === 'arrow') {
      arrowOps.deleteArrow(arrowId(entityId));
    } else {
      nodeOps.deleteNode(nodeId(entityId));
    }
    clearSelection();
  };

  if (!panelConfig) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center space-x-2 border-b pb-2">
          <Settings className="w-5 h-5" />
          <h3 className="text-lg font-semibold">Unknown Node Type</h3>
        </div>
        <div className="space-y-4">
          <div className="text-red-500">No configuration found for node type: {nodeType}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between border-b pb-2">
        <div className="flex items-center space-x-2">
          <span>{nodeConfig?.icon || '⚙️'}</span>
          <h3 className="text-lg font-semibold">
            {nodeConfig?.label ? `${nodeConfig.label} Properties` : `${nodeType} Properties`}
          </h3>
        </div>
        <button
          onClick={handleDelete}
          className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Delete"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
      <div className="space-y-4">
        <Form>
          {panelConfig.layout === 'twoColumn' ? (
            <TwoColumnPanelLayout
              leftColumn={renderSection(panelConfig.leftColumn)}
              rightColumn={renderSection(panelConfig.rightColumn)}
            />
          ) : panelConfig.layout === 'single' ? (
            <SingleColumnPanelLayout>
              {renderSection(panelConfig.fields)}
            </SingleColumnPanelLayout>
          ) : (
            renderSection(panelConfig.fields)
          )}
        </Form>
      </div>
    </div>
  );
});

PropertyPanel.displayName = 'PropertyPanel';