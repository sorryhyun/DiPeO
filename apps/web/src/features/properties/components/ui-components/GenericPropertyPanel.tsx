import React, { useState, useEffect } from 'react';
import { PanelConfig, FieldConfig } from '@/shared/types/panelConfig';
import { usePropertyPanel } from '@/features/properties';
import {
  Form,
  TwoColumnPanelLayout,
  SingleColumnPanelLayout,
  FormRow,
  InlineTextField,
  InlineSelectField,
  TextAreaField,
  CheckboxField,
  IterationCountField,
  PersonSelectionField,
  LabelPersonRow,
  VariableDetectionTextArea
} from './FormComponents';

interface GenericPropertyPanelProps<T extends Record<string, any>> {
  nodeId: string;
  data: T;
  config: PanelConfig<T>;
}

export const GenericPropertyPanel = <T extends Record<string, any>>({
  nodeId,
  data,
  config
}: GenericPropertyPanelProps<T>) => {
  // State for async options
  const [asyncOptions, setAsyncOptions] = useState<Record<string, Array<{ value: string; label: string }>>>({});
  
  // Determine entity type based on data.type
  const getEntityType = (dataType: string): 'node' | 'arrow' | 'person' => {
    if (dataType === 'arrow') return 'arrow';
    if (dataType === 'person') return 'person';
    return 'node';
  };
  
  const entityType = getEntityType(data.type);
  const { formData, handleChange } = usePropertyPanel<T>(nodeId, entityType, data);
  
  // Load async options when component mounts or when dependencies change
  useEffect(() => {
    const loadAsyncOptions = async () => {
      const fieldsToProcess: FieldConfig[] = [];
      
      // Collect all fields that need async options
      const collectFields = (fields: FieldConfig[]) => {
        fields.forEach(field => {
          if (field.type === 'select' && typeof field.options === 'function') {
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
      
      // Load options for all async fields
      const optionsMap: Record<string, Array<{ value: string; label: string }>> = {};
      
      for (const field of fieldsToProcess) {
        try {
          if (field.type === 'select' && typeof field.options === 'function' && field.name) {
            let result;
            
            // Check if the options function expects formData (for dependent fields)
            if (field.options.length > 0) {
              // Function expects formData parameter
              result = (field.options as (formData: any) => Promise<Array<{ value: string; label: string }>>)(formData);
            } else {
              // Function doesn't expect parameters
              result = (field.options as () => Promise<Array<{ value: string; label: string }>> | Array<{ value: string; label: string }>)();
            }
            
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
  }, [config, formData]); // Added formData as dependency
  
  // Reload options for dependent fields when their dependencies change
  useEffect(() => {
    const reloadDependentOptions = async () => {
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
      
      if (config.fields) {
        collectDependentFields(config.fields);
      }
      if (config.leftColumn) {
        collectDependentFields(config.leftColumn);
      }
      if (config.rightColumn) {
        collectDependentFields(config.rightColumn);
      }
      
      // Check if any dependent fields need updating
      const updatedOptions: Record<string, Array<{ value: string; label: string }>> = {};
      let hasUpdates = false;
      
      for (const field of fieldsToUpdate) {
        if (field.type === 'select' && field.dependsOn && field.name && typeof field.options === 'function') {
          // Check if any dependency has changed (we'll reload all for simplicity)
          try {
            let result;
            
            if (field.options.length > 0) {
              result = (field.options as (formData: any) => Promise<Array<{ value: string; label: string }>>)(formData);
            } else {
              result = (field.options as () => Promise<Array<{ value: string; label: string }>> | Array<{ value: string; label: string }>)();
            }
            
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
    };
    
    reloadDependentOptions();
  }, [formData.service, formData.apiKeyId]); // Only trigger when these specific dependencies change
  
  // Type-safe update function
  const updateField = (name: string, value: any) => {
    handleChange(name as keyof T, value);
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
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
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
                result = (fieldConfig.options as (formData: any) => Promise<Array<{ value: string; label: string }>>)(formData);
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
        
        return (
          <InlineSelectField
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            options={options}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
          />
        );
      }

      case 'textarea': {
        return (
          <TextAreaField
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            rows={fieldConfig.rows}
            placeholder={fieldConfig.placeholder}
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
          />
        );
      }

      case 'variableTextArea': {
        return (
          <VariableDetectionTextArea
            key={key}
            label={fieldConfig.label || ''}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            rows={fieldConfig.rows}
            placeholder={fieldConfig.placeholder}
            detectedVariables={data.detectedVariables}
          />
        );
      }

      case 'labelPersonRow': {
        return (
          <LabelPersonRow
            key={key}
            labelValue={formData.label || ''}
            onLabelChange={(v) => updateField('label', v)}
            personValue={formData.personId || ''}
            onPersonChange={(v) => updateField('personId', v)}
            labelPlaceholder={fieldConfig.labelPlaceholder}
            personPlaceholder={fieldConfig.personPlaceholder}
          />
        );
      }

      case 'iterationCount': {
        return (
          <IterationCountField
            key={key}
            value={formData[fieldConfig.name] || 1}
            onChange={(v) => updateField(fieldConfig.name, v)}
            min={fieldConfig.min}
            max={fieldConfig.max}
            label={fieldConfig.label}
            className={fieldConfig.className}
          />
        );
      }

      case 'personSelect': {
        return (
          <PersonSelectionField
            key={key}
            value={formData[fieldConfig.name] || ''}
            onChange={(v) => updateField(fieldConfig.name, v)}
            placeholder={fieldConfig.placeholder}
            className={fieldConfig.className}
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
        const CustomComponent = fieldConfig.component;
        return (
          <CustomComponent
            key={key}
            formData={formData}
            handleChange={updateField}
            {...fieldConfig.props}
          />
        );
      }

      default:
        console.warn(`Unknown field type: ${(fieldConfig as any).type}`);
        return null;
    }
  };

  // Render based on layout
  if (config.layout === 'single') {
    return (
      <Form>
        <SingleColumnPanelLayout>
          {config.fields?.map((field, index) => renderField(field, index))}
        </SingleColumnPanelLayout>
      </Form>
    );
  }

  return (
    <Form>
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