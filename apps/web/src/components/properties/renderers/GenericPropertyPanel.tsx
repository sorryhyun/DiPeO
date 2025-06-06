import React, { useState, useEffect, useRef } from 'react';
import { PanelConfig, PanelFieldConfig, PropertyFieldConfig, SelectFieldConfig } from '@/types';
import { usePropertyManager } from '@/hooks/usePropertyManager';
import { useIsReadOnly } from '@/hooks/useStoreSelectors';
import { UnifiedFormField } from '../fields';
import { Form, FormRow, TwoColumnPanelLayout, SingleColumnPanelLayout } from '../fields/FormComponents';
import { preInitializeModel } from '@/utils/api';

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
  const { formData, updateField: updateFormField } = usePropertyManager<T>(nodeId, entityType, data, {
    autoSave: true,
    autoSaveDelay: 500
  });
  
  // Create a handleChange wrapper for compatibility
  const handleChange = (name: string, value: unknown) => {
    updateFormField(name as keyof T, value as T[keyof T]);
  };
  
  // Load async options when component mounts - only for non-dependent fields
  useEffect(() => {
    const loadAsyncOptions = async () => {
      const fieldsToProcess: SelectFieldConfig[] = [];
      
      // Collect fields that need async options but are NOT dependent on formData
      const collectFields = (fields: PanelFieldConfig[]) => {
        fields.forEach(field => {
          if (field.type === 'select' && typeof field.options === 'function' && !field.dependsOn) {
            fieldsToProcess.push(field as SelectFieldConfig);
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
            const optionsFn = field.options as () => Promise<Array<{ value: string; label: string }>> | Array<{ value: string; label: string }>;
            const result = optionsFn();
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
        const fieldsToUpdate: SelectFieldConfig[] = [];
        
        // Collect fields that have dependencies
        const collectDependentFields = (fields: PanelFieldConfig[]) => {
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
              const optionsFn = field.options as (formData: T) => Promise<Array<{ value: string; label: string }>>;
              const result = optionsFn(formData);
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
    handleChange(name, value);
    
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
  
  // Convert PanelFieldConfig to PropertyFieldConfig
  const convertPanelFieldConfig = (fieldConfig: PanelFieldConfig): PropertyFieldConfig | null => {
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
    
    // Handle special field types that don't have direct property field equivalents
    if (fieldConfig.type === 'row' || fieldConfig.type === 'custom' || fieldConfig.type === 'labelPersonRow') {
      return null;
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
      case 'maxIteration':
        type = 'number';
        min = fieldConfig.min;
        max = fieldConfig.max;
        break;
      case 'personSelect':
        type = 'person';
        break;
      default:
        return null;
    }
    
    // Get options for select fields
    let options: PropertyFieldConfig['options'];
    if (fieldConfig.type === 'select' && fieldConfig.name) {
      if (Array.isArray(fieldConfig.options)) {
        options = fieldConfig.options;
      } else if (asyncOptions[fieldConfig.name]) {
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
    if ('disabled' in fieldConfig) {
      baseField.disabled = fieldConfig.disabled;
    }
    
    baseField.customProps = {
      disabled: isMonitorMode || baseField.disabled || false,
      detectedVariables: data.detectedVariables as string[] | undefined
    };
    
    return baseField;
  };
  
  // Field renderer function using UnifiedFormField
  const renderField = (fieldConfig: PanelFieldConfig, index: number): React.ReactNode => {
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
          <UnifiedFormField
            type="text"
            name="label"
            label="Label"
            value={(formData as Record<string, unknown>).label}
            onChange={(v) => updateField('label', v)}
            placeholder={fieldConfig.labelPlaceholder}
            disabled={isMonitorMode}
          />
          <UnifiedFormField
            type="person-select"
            name="personId"
            label="Person"
            value={(formData as Record<string, unknown>).personId}
            onChange={(v) => updateField('personId', v)}
            placeholder={fieldConfig.personPlaceholder}
            disabled={isMonitorMode}
          />
        </FormRow>
      );
    }
    
    // Convert to PropertyFieldConfig for standard fields
    const convertedConfig = convertPanelFieldConfig(fieldConfig);
    if (!convertedConfig) return null;
    
    // Map field types to UnifiedFormField types
    const getFieldType = () => {
      switch (convertedConfig.type) {
        case 'string':
          if (fieldConfig.type === 'variableTextArea') {
            return 'variable-textarea';
          }
          return convertedConfig.multiline ? 'textarea' : 'text';
        case 'select':
          return 'select';
        case 'boolean':
          return 'checkbox';
        case 'number':
          return fieldConfig.type === 'maxIteration' ? 'iteration-count' : 'number';
        case 'person':
          return 'person-select';
        case 'file':
          return 'file';
        default:
          return 'text';
      }
    };
    
    const fieldValue = fieldConfig.name ? formData[fieldConfig.name as keyof T] : undefined;
    
    return (
      <UnifiedFormField
        key={key}
        type={getFieldType()}
        name={convertedConfig.name}
        label={convertedConfig.label}
        value={fieldValue}
        onChange={(v) => updateField(convertedConfig.name, v)}
        placeholder={convertedConfig.placeholder}
        options={convertedConfig.options}
        disabled={isMonitorMode}
        required={convertedConfig.isRequired}
        min={convertedConfig.min}
        max={convertedConfig.max}
        helperText={convertedConfig.helperText}
        acceptedFileTypes={convertedConfig.acceptedFileTypes}
        detectedVariables={data.detectedVariables as string[] | undefined}
        className={fieldConfig.className}
        rows={fieldConfig.type === 'textarea' || fieldConfig.type === 'variableTextArea' ? fieldConfig.rows : undefined}
      />
    );
  };
  
  const renderSection = (fields: PanelFieldConfig[] | undefined) => {
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