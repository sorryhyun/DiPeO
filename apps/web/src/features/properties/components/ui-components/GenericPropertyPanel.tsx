import React, { useState, useEffect, useRef } from 'react';
import { PanelConfig, FieldConfig } from '@/common/types/panelConfig';
import { usePropertyPanel } from '@/features/properties';
import {
  Form,
  TwoColumnPanelLayout,
  SingleColumnPanelLayout,
  FormRow,
  InlineTextField,
  InlineSelectField,
  TextAreaField,
  CheckboxField
} from '@/common/components/forms';
import {
  IterationCountField,
  PersonSelectionField,
  LabelPersonRow,
  VariableDetectionTextArea
} from './FormComponents';
import { preInitializeModel } from '@/features/properties/utils/propertyHelpers';
import { useMonitorStore } from '@/state/stores';

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
  const isMonitorMode = useMonitorStore(state => state.isMonitorMode);
  
  // Determine entity type based on data.type
  const getEntityType = (dataType: unknown): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);
  const { formData, handleChange } = usePropertyPanel<T>(nodeId, entityType, data);
  
  // Log formData state for person property panel
  React.useEffect(() => {
  }, [formData, data.type, nodeId]);
  
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
            // Non-dependent fields should not expect formData parameter
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
        
        // Log dependency change if this is person property panel
        
        for (const field of fieldsToUpdate) {
          if (field.type === 'select' && field.dependsOn && field.name && typeof field.options === 'function') {
            try {
              // Dependent fields expect formData parameter
              const result = (field.options as (formData: T) => Promise<Array<{ value: string; label: string }>>)(formData);
              const options = result instanceof Promise ? await result : result;
              updatedOptions[field.name] = options;
              hasUpdates = true;
              
              // Log model options fetch if this is the model field
            } catch (error) {
              console.error(`[Person Property Panel] Failed to reload options for dependent field ${field.name}:`, error);
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
      console.log('[Person Property Panel] Model selection detected:', {
        name,
        value,
        formDataService: formData.service,
        formDataApiKeyId: formData.apiKeyId,
        dataService: data.service,
        dataApiKeyId: data.apiKeyId
      });
      
      // Check both formData and data for required fields
      const service = formData.service || data.service;
      const apiKeyId = formData.apiKeyId || data.apiKeyId;
      
      if (service && value && apiKeyId) {
        console.log('[Person Property Panel] Pre-initializing model with:', {
          service,
          model: value,
          apiKeyId
        });
        try {
          await preInitializeModel(
            service as string,
            value as string,
            apiKeyId as string
          );
        } catch (error) {
          console.warn('[Person Property Panel] Failed to pre-initialize model:', error);
        }
      } else {
        console.log('[Person Property Panel] Missing required fields for pre-initialization:', {
          service,
          value,
          apiKeyId
        });
      }
    }
  };
  
  // Field renderer function
  const renderField = (fieldConfig: FieldConfig, index: number): React.ReactNode => {

    
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

    const key = fieldConfig.name ? `${fieldConfig.name}-${index}` : `field-${index}`;

    switch (fieldConfig.type) {
      case 'text': {
        return (
          <InlineTextField
            key={key}
            label={fieldConfig.label || ''}
            value={String(formData[fieldConfig.name] || '')}
            onChange={(v) => updateField(fieldConfig.name, v)}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
            disabled={isMonitorMode || fieldConfig.disabled}
          />
        );
      }

      case 'select': {
        let options: Array<{ value: string; label: string }> = [];
        
        if (Array.isArray(fieldConfig.options)) {
          options = fieldConfig.options as Array<{ value: string; label: string }>;
        } else if (typeof fieldConfig.options === 'function') {
          // Check if we have loaded async options for this field
          if (fieldConfig.name && asyncOptions[fieldConfig.name]) {
            options = asyncOptions[fieldConfig.name] || [];
          } else {
            // Try to call the function synchronously as a fallback
            try {
              let result;
              if (fieldConfig.options.length > 0) {
                // Function expects formData parameter
                result = (fieldConfig.options as (formData: T) => Promise<Array<{ value: string; label: string }>>)(formData);
              } else {
                // Function doesn't expect parameters
                result = (fieldConfig.options as () => Promise<Array<{ value: string; label: string }>> | Array<{ value: string; label: string }>)();
              }
              
              if (result instanceof Promise) {
                // For async functions not yet loaded, show empty options
                options = [];
              } else {
                options = result as Array<{ value: string; label: string }>;
              }
            } catch (error) {
              console.error(`Error getting options for ${fieldConfig.name}:`, error);
              options = [];
            }
          }
        }

        
        // For person service field, add the value to the key to force re-render
        const selectKey = data.type === 'person' && fieldConfig.name === 'service' 
          ? `${key}-${formData[fieldConfig.name]}`
          : key;
        
        return (
          <InlineSelectField
            key={selectKey}
            label={fieldConfig.label || ''}
            value={String(formData[fieldConfig.name] || '')}
            onChange={(v) => {
              updateField(fieldConfig.name, v);
            }}
            options={options}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
            isDisabled={isMonitorMode}
          />
        );
      }

      case 'textarea': {
        return (
          <TextAreaField
            key={key}
            label={fieldConfig.label || ''}
            value={String(formData[fieldConfig.name] || '')}
            onChange={(v) => updateField(fieldConfig.name, v)}
            rows={fieldConfig.rows}
            placeholder={fieldConfig.placeholder}
            disabled={isMonitorMode}
          />
        );
      }

      case 'checkbox': {
        return (
          <CheckboxField
            key={key}
            label={fieldConfig.label || ''}
            checked={!!formData[fieldConfig.name]}
            onChange={(checked) => updateField(fieldConfig.name, checked)}
            disabled={isMonitorMode}
          />
        );
      }

      case 'variableTextArea': {
        return (
          <VariableDetectionTextArea
            key={key}
            label={fieldConfig.label || ''}
            value={String(formData[fieldConfig.name] || '')}
            onChange={(v) => updateField(fieldConfig.name, v)}
            rows={fieldConfig.rows}
            placeholder={fieldConfig.placeholder}
            detectedVariables={data.detectedVariables as string[] | undefined}
            disabled={isMonitorMode}
          />
        );
      }

      case 'labelPersonRow': {
        return (
          <LabelPersonRow
            key={key}
            labelValue={String(formData.label || '')}
            onLabelChange={(v) => updateField('label', v)}
            personValue={String(formData.personId || '')}
            onPersonChange={(v) => updateField('personId', v)}
            labelPlaceholder={fieldConfig.labelPlaceholder}
            personPlaceholder={fieldConfig.personPlaceholder}
            disabled={isMonitorMode}
          />
        );
      }

      case 'iterationCount': {
        return (
          <IterationCountField
            key={key}
            value={Number(formData[fieldConfig.name]) || 1}
            onChange={(v) => updateField(fieldConfig.name, v)}
            min={fieldConfig.min}
            max={fieldConfig.max}
            label={fieldConfig.label}
            className={fieldConfig.className}
            disabled={isMonitorMode}
          />
        );
      }

      case 'personSelect': {
        return (
          <PersonSelectionField
            key={key}
            value={String(formData[fieldConfig.name] || '')}
            onChange={(v) => updateField(fieldConfig.name, v)}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
            disabled={isMonitorMode}
          />
        );
      }

      case 'row': {
        return (
          <FormRow key={key} className={fieldConfig.className}>
            {fieldConfig.fields.map((field, fieldIndex) => renderField(field, fieldIndex))}
          </FormRow>
        );
      }

      case 'custom': {
        // For complex custom components
        const CustomComponent = fieldConfig.component as React.ComponentType<{
          formData: T;
          handleChange: (name: string, value: unknown) => Promise<void>;
          [key: string]: unknown;
        }>;
        return (
          <CustomComponent
            key={key}
            formData={formData}
            handleChange={updateField}
            {...(fieldConfig.props || {})}
          />
        );
      }

      default:
        console.warn(`Unknown field type: ${(fieldConfig as FieldConfig & { type: string }).type}`);
        return null;
    }
  };

  // Render based on layout
  if (config.layout === 'single') {
    return (
      <Form>
        {isMonitorMode && (
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center justify-between">
              <p className="text-xs text-blue-700 font-medium">
                📊 Monitor Mode - Properties are read-only
              </p>
              <button
                onClick={() => useMonitorStore.getState().clearMonitorDiagram()}
                className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded"
              >
                Exit Monitor Mode
              </button>
            </div>
          </div>
        )}
        <SingleColumnPanelLayout>
          {config.fields?.map((field, index) => renderField(field, index))}
        </SingleColumnPanelLayout>
      </Form>
    );
  }

  return (
    <Form>
      {isMonitorMode && (
        <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex items-center justify-between">
            <p className="text-xs text-blue-700 font-medium">
              📊 Monitor Mode - Properties are read-only
            </p>
            <button
              onClick={() => useMonitorStore.getState().clearMonitorDiagram()}
              className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded"
            >
              Exit Monitor Mode
            </button>
          </div>
        </div>
      )}
      <TwoColumnPanelLayout
        leftColumn={
          <>{config.leftColumn?.map((field, index) => renderField(field, index))}</>
        }
        rightColumn={
          <>{config.rightColumn?.map((field, index) => renderField(field, index))}</>
        }
      />
    </Form>
  );
};