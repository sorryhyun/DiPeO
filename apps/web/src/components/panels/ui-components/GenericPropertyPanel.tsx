import React, { useState, useEffect, useRef } from 'react';
import { PanelConfig, FieldConfig } from '../../../../types';
import { usePropertyPanel } from '../..';
import { PropertyFieldConfig } from '../../../../types';
import { preInitializeModel } from '../../utils/propertyHelpers';
import { useIsReadOnly } from '../../../../common/utils/storeSelectors';
import { Input, Select, Switch } from '../../../../common/components';
import { renderInlineField, renderTextAreaField, isTextAreaField } from '../../utils/fieldRenderers';

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
  // State for async options
  const [asyncOptions, setAsyncOptions] = useState<Record<string, Array<{ value: string; label: string }>>>({});
  
  // Track previous dependencies to avoid unnecessary API calls
  const prevDepsRef = useRef<{ service?: string; apiKeyId?: string }>({});
  
  // Check if we're in monitor mode (read-only)
  const isMonitorMode = useIsReadOnly();
  
  // Determine entity type based on data.type
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);
  const { formData, handleChange } = usePropertyPanel<T>(nodeId, entityType, data);
  
  // Load async options when component mounts - only for non-dependent fields
  useEffect(() => {
    const loadAsyncOptions = async () => {
      const fieldsToProcess: FieldConfig[] = [];
      
      // Collect fields that need async options but are NOT dependent on formData
      const collectFields = (fields: FieldConfig[]) => {
        fields.forEach(field => {
          if (field.type === 'select' && typeof field.options === 'function' && !field.dependsOn) {
            fieldsToProcess.push(field);
          } else if (field.type === 'row' && field.fields) {
            collectFields(field.fields);
          }
        });
      };
      
      if (config.fields) {
        collectFields(config.fields);
      }
      if (config.leftColumn) {
        collectFields(config.leftColumn);
      }
      if (config.rightColumn) {
        collectFields(config.rightColumn);
      }
      
      // Load options for non-dependent async fields
      const optionsMap: Record<string, Array<{ value: string; label: string }>> = {};
      
      for (const field of fieldsToProcess) {
        try {
          if (field.type === 'select' && typeof field.options === 'function' && field.name) {
            const result = (field.options as () => Promise<Array<{ value: string; label: string }>> | Array<{ value: string; label: string }>)();
            const options = result instanceof Promise ? await result : result;
            optionsMap[field.name] = options;
          }
        } catch (error) {
          console.error(`Failed to load options for field ${field.name}:`, error);
          if (field.name) {
            optionsMap[field.name] = [];
          }
        }
      }
      
      setAsyncOptions(optionsMap);
    };
    
    loadAsyncOptions();
  }, [config]);
  
  // Ref to track if dependent options reload is in progress
  const reloadInProgressRef = useRef(false);
  
  // Reload options for dependent fields when their dependencies change
  useEffect(() => {
    const reloadDependentOptions = async () => {
      // Check if dependencies actually changed
      const currentService = formData.service as string;
      const currentApiKeyId = formData.apiKeyId as string;
      
      if (prevDepsRef.current.service === currentService && 
          prevDepsRef.current.apiKeyId === currentApiKeyId) {
        return; // No change in dependencies
      }
      
      // Prevent multiple simultaneous calls
      if (reloadInProgressRef.current) {
        return;
      }
      
      reloadInProgressRef.current = true;
      prevDepsRef.current = { service: currentService, apiKeyId: currentApiKeyId };
      
      try {
        const fieldsToUpdate: FieldConfig[] = [];
        
        // Collect fields that have dependencies
        const collectDependentFields = (fields: FieldConfig[]) => {
          fields.forEach(field => {
            if (field.type === 'select' && field.dependsOn && typeof field.options === 'function') {
              fieldsToUpdate.push(field);
            } else if (field.type === 'row' && field.fields) {
              collectDependentFields(field.fields);
            }
          });
        };
        
        collectDependentFields(config.fields || []);
        collectDependentFields(config.leftColumn || []);
        collectDependentFields(config.rightColumn || []);
        
        // Only proceed if we have dependent fields to update
        if (fieldsToUpdate.length === 0) return;
        
        // Check if any dependent fields need updating
        const updatedOptions: Record<string, Array<{ value: string; label: string }>> = {};
        let hasUpdates = false;
        
        for (const field of fieldsToUpdate) {
          if (field.type === 'select' && field.dependsOn && field.name && typeof field.options === 'function') {
            try {
              // Dependent fields expect formData parameter
              const result = (field.options as (formData: T) => Promise<Array<{ value: string; label: string }>>)(formData);
              const options = result instanceof Promise ? await result : result;
              updatedOptions[field.name] = options;
              hasUpdates = true;
            } catch (error) {
              console.error(`Failed to reload options for dependent field ${field.name}:`, error);
              updatedOptions[field.name] = [];
              hasUpdates = true;
            }
          }
        }
        
        if (hasUpdates) {
          setAsyncOptions(prev => ({ ...prev, ...updatedOptions }));
        }
      } finally {
        reloadInProgressRef.current = false;
      }
    };
    
    reloadDependentOptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.service, formData.apiKeyId]); // Only trigger when service or API key changes - other deps are stable
  
  // Type-safe update function with model pre-initialization
  const updateField = async (name: string, value: unknown) => {
    // Skip updates if in monitor mode (read-only)
    if (isMonitorMode) {
      return;
    }

    // Update the form data - always allow updating fields (including new optional fields)
    handleChange(name as keyof T, value as T[keyof T]);
    
    // If this is a model selection for a person entity and we have all required data, pre-initialize the model
    if (data.type === 'person' && name === 'modelName') {
      // Check both formData and data for required fields
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
  };
  
  // Convert FieldConfig to PropertyFieldConfig
  const convertFieldConfig = (fieldConfig: FieldConfig): PropertyFieldConfig | null => {
    // Check conditional rendering
    if (fieldConfig.conditional) {
      const fieldValue = formData[fieldConfig.conditional.field];
      const { values, operator = 'includes' } = fieldConfig.conditional;
      
      let shouldRender = false;
      switch (operator) {
        case 'equals':
          shouldRender = values.includes(fieldValue);
          break;
        case 'notEquals':
          shouldRender = !values.includes(fieldValue);
          break;
        case 'includes':
        default:
          shouldRender = values.includes(fieldValue);
          break;
      }
      
      if (!shouldRender) return null;
    }
    
    // Convert special field types to unified types
    let type: PropertyFieldConfig['type'] = 'string';
    let multiline = false;
    let min: number | undefined;
    let max: number | undefined;
    
    switch (fieldConfig.type) {
      case 'text':
        type = 'string';
        break;
      case 'select':
        type = 'select';
        break;
      case 'textarea':
      case 'variableTextArea':
        type = 'string';
        multiline = true;
        break;
      case 'checkbox':
        type = 'boolean';
        break;
      case 'iterationCount':
        type = 'number';
        min = fieldConfig.min;
        max = fieldConfig.max;
        break;
      case 'labelPersonRow':
      case 'personSelect':
        type = 'person';
        break;
      default:
        return null;
    }
    
    // Get options for select fields
    let options: PropertyFieldConfig['options'];
    if (fieldConfig.type === 'select') {
      if (Array.isArray(fieldConfig.options)) {
        options = fieldConfig.options;
      } else if (fieldConfig.name && asyncOptions[fieldConfig.name]) {
        options = asyncOptions[fieldConfig.name];
      }
    }
    
    const baseField: PropertyFieldConfig = {
      name: fieldConfig.name || '',
      label: fieldConfig.label || '',
      type,
      options,
      multiline,
      min,
      max
    };
    
    // Add optional properties based on field type
    if ('placeholder' in fieldConfig) {
      baseField.placeholder = fieldConfig.placeholder;
    }
    if ('required' in fieldConfig) {
      baseField.isRequired = (fieldConfig as any).required;
    }
    if ('helperText' in fieldConfig) {
      baseField.helperText = (fieldConfig as any).helperText;
    }
    if ('acceptedFileTypes' in fieldConfig) {
      baseField.acceptedFileTypes = (fieldConfig as any).acceptedFileTypes;
    }
    
    baseField.customProps = {
      disabled: isMonitorMode || ('disabled' in fieldConfig ? fieldConfig.disabled : false),
      detectedVariables: data.detectedVariables as string[] | undefined
    };
    
    return baseField;
  };
  
  // Field renderer function using UnifiedFieldRenderer
  const renderField = (fieldConfig: FieldConfig, index: number): React.ReactNode => {
    const convertedConfig = convertFieldConfig(fieldConfig);
    if (!convertedConfig) return null;
    
    const key = fieldConfig.name ? `${fieldConfig.name}-${index}` : `field-${index}`;
    
    // Handle special cases
    if (fieldConfig.type === 'row' && fieldConfig.fields) {
      return (
        <FormRow key={key} className={fieldConfig.className}>
          {fieldConfig.fields.map((field, idx) => renderField(field, idx))}
        </FormRow>
      );
    }
    
    if (fieldConfig.type === 'labelPersonRow') {
      // Render two fields in a row
      return (
        <FormRow key={key}>
          <UnifiedFieldRenderer
            field={{
              name: 'label',
              label: 'Label',
              type: 'string',
              placeholder: fieldConfig.labelPlaceholder
            }}
            value={formData.label}
            onChange={(v) => updateField('label', v)}
          />
          <UnifiedFieldRenderer
            field={{
              name: 'personId',
              label: 'Person',
              type: 'person',
              placeholder: fieldConfig.personPlaceholder
            }}
            value={formData.personId}
            onChange={(v) => updateField('personId', v)}
          />
        </FormRow>
      );
    }
    
    return (
      <UnifiedFieldRenderer
        key={key}
        field={convertedConfig}
        value={formData[convertedConfig.name]}
        onChange={(v) => updateField(convertedConfig.name, v)}
        nodeData={data}
        className={fieldConfig.className}
      />
    );
  };
  
  const renderSection = (fields: FieldConfig[] | undefined) => {
    if (!fields) return null;
    return fields.map((field, index) => renderField(field, index));
  };
  
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