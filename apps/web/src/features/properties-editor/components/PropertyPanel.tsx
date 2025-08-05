import React, { useCallback, useMemo } from 'react';
import { Settings, Trash2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Dict, DomainPerson, nodeId, arrowId, personId } from '@/core/types';
import type { ArrowData } from '@/lib/graphql/types';
import { PanelLayoutConfig, TypedPanelFieldConfig } from '@/features/diagram-editor/types/panel';
import { getNodeConfig } from '@/features/diagram-editor/config/nodes';
import { derivePanelConfig } from '@/core/config/unifiedConfig';
import { ENTITY_PANEL_CONFIGS } from '../config';
import { FIELD_TYPES } from '@/core/types/panel';
import { useCanvasOperations, useCanvasState } from '@/shared/contexts/CanvasContext';
import { usePropertyManager } from '../hooks';
import { UnifiedFormField, type FieldValue, type UnifiedFieldType } from './fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from './fields/FormComponents';
import { apolloClient } from '@/lib/graphql/client';
import { GetApiKeysDocument, UpdatePersonDocument, type GetApiKeysQuery } from '@/__generated__/graphql';

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
  // Convert uppercase node types from GraphQL to lowercase for config lookup
  const normalizedNodeType = typeof nodeType === 'string' ? nodeType.toLowerCase() : nodeType;
  const nodeConfig = getNodeConfig(normalizedNodeType);
  const queryClient = useQueryClient();
  
  // Debug logging for node config lookup
  if (!nodeConfig && nodeType !== 'arrow' && nodeType !== 'person') {
    console.warn(`No config found for node type: ${nodeType} (normalized: ${normalizedNodeType})`);
  }
  
  // Use context instead of individual hooks
  const { nodeOps, arrowOps, personOps, clearSelection } = useCanvasOperations();
  const { personsWithUsage } = useCanvasState();
  
  // Get panel config from the new unified configuration
  let panelConfig = null;
  if (nodeType === 'arrow' || nodeType === 'person') {
    panelConfig = ENTITY_PANEL_CONFIGS[nodeType];
  } else if (nodeConfig) {
    panelConfig = derivePanelConfig(nodeConfig);
  }
  
  const personsForSelect = personsWithUsage.map(person => ({ id: person.id, label: person.label }));
  
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);

  // Flatten the data for form fields if it's a person - memoize to prevent infinite loops
  const flattenedData = useMemo(() => {
    return entityType === 'person' 
      ? ensurePersonFields(flattenObject(data as Record<string, unknown>)) 
      : data;
  }, [entityType, data]);

  const {
    formData,
    updateField,
    updateFormData,
    processedFields,
    isReadOnly
  } = usePropertyManager(entityId, entityType, flattenedData as Record<string, unknown>, {
    autoSave: true,
    autoSaveDelay: 100, // Increased from 500ms to 1000ms to prevent race conditions
    panelConfig: panelConfig as PanelLayoutConfig<Record<string, unknown>>
  });

  const handleFieldUpdate = useCallback(async (name: string, value: unknown) => {
    // For API key changes, batch the updates to prevent race conditions
    if (data.type === 'person' && name === 'llm_config.api_key_id') {
      // Create a batch update
      const updates: Record<string, unknown> = {
        [name]: value,
        'llm_config.model': '', // Clear model when API key changes
      };
      
      if (value) {
        try {
          const { data: apiKeysData } = await apolloClient.query<GetApiKeysQuery>({
            query: GetApiKeysDocument,
            fetchPolicy: 'network-only'  // Always fetch fresh data to avoid stale API keys
          });
          const selectedKey = apiKeysData.api_keys.find((k) => k.id === value);
          if (selectedKey) {
            updates['llm_config.service'] = selectedKey.service;
          } else {
          }
        } catch (error) {
          console.error('Failed to update service:', error);
        }
      }
      
      // Update form data immediately
      updateFormData(updates);
      
      // Then invalidate model options cache after a small delay to ensure data is updated
      setTimeout(() => {
        queryClient.invalidateQueries({ 
          queryKey: ['field-options', entityType, entityId, 'llm_config.model'],
          exact: false
        });
      }, 100);
      return;
    }
    
    // Regular field update
    updateField(name, value);
    
    if (data.type === 'person' && name === 'llm_config.model' && value) {
      const apiKeyIdStr = formData['llm_config.api_key_id'] as string;
      
      // Only proceed if we have an API key
      if (!apiKeyIdStr) {
        console.warn('Cannot set model without an API key');
        updateField('llm_config.model', undefined);
        return;
      }
      
      // Update the person's model directly without requiring saved diagram
      try {
        const personData = data as DomainPerson;
        const { data: updateResult } = await apolloClient.mutate({
          mutation: UpdatePersonDocument,
          variables: { 
            id: entityId,
            input: {
              llm_config: {
                service: personData.llm_config.service,
                model: value as string,
                api_key_id: apiKeyIdStr,
                system_prompt: personData.llm_config.system_prompt
              }
            }
          }
        });
        
        if (!updateResult?.update_person?.success) {
          console.error('Failed to update model:', updateResult?.update_person?.message);
        } else {
          console.log('Model updated successfully:', value);
        }
      } catch (error) {
        console.error('Error initializing model:', error);
      }
    }
    
    // Don't manually sync other fields - let auto-save handle everything
  }, [updateField, updateFormData, formData, data, entityId, queryClient]);

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
        adjustable={fieldConfig.adjustable}
        onPromptFileSelect={fieldConfig.showPromptFileButton ? (content: string, filename: string) => {
          // Update the prompt_file field with the filename
          handleFieldUpdate('prompt_file', filename);
        } : undefined}
      />
    );
  }, [formData, handleFieldUpdate, isReadOnly, personsForSelect, shouldRenderField, processedFields]);

  const renderSection = useCallback((fields: TypedPanelFieldConfig<Record<string, unknown>>[] | undefined) => {
    if (!fields) {
      return null;
    }
    return fields.map((field, index) => renderField(field, index));
  }, [renderField]);

  const handleDelete = async () => {
    if (data.type === 'person') {
      await personOps.deletePerson(personId(entityId));
    } else if (data.type === 'arrow') {
      await arrowOps.deleteArrow(arrowId(entityId));
    } else {
      await nodeOps.deleteNode(nodeId(entityId));
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
        <div className="flex items-center space-x-2 flex-1">
          <span>{nodeConfig?.icon || '⚙️'}</span>
          <h3 className="text-lg font-semibold whitespace-nowrap">
            {nodeConfig?.label || `${nodeType}`} Properties
          </h3>
          {/* Universal label field for all nodes */}
          {(entityType === 'node' || entityType === 'arrow') && (
            <div className="flex-1 ml-4">
              <UnifiedFormField
                type="text"
                name="label"
                label=""
                value={formData.label as FieldValue}
                onChange={(v) => handleFieldUpdate('label', v)}
                placeholder="Enter label"
                disabled={isReadOnly}
              />
            </div>
          )}
        </div>
        <button
          onClick={handleDelete}
          className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors ml-2"
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