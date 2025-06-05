import React from 'react';
import { UnifiedFormField } from './UnifiedFormField';
import { PropertyFieldConfig } from '../../types/fieldConfig';
import { usePersons } from '@/common/utils/storeSelectors';

interface UnifiedFieldRendererProps {
  field: PropertyFieldConfig;
  value: any;
  onChange: (value: any) => void;
  nodeData?: any;
  layout?: 'inline' | 'vertical';
  className?: string;
}

/**
 * Unified field renderer that maps PropertyFieldConfig to UnifiedFormField.
 * This replaces the duplicate rendering logic across the codebase.
 */
export const UnifiedFieldRenderer: React.FC<UnifiedFieldRendererProps> = ({
  field,
  value,
  onChange,
  nodeData,
  layout = 'inline',
  className
}) => {
  const persons = usePersons();
  
  // Map field types to unified form field types
  const getFieldType = () => {
    switch (field.type) {
      case 'string':
        return field.multiline ? 'textarea' : 'text';
      case 'select':
        return 'select';
      case 'boolean':
        return 'checkbox';
      case 'number':
        return field.name === 'iterationCount' ? 'iteration-count' : 'number';
      case 'person':
        return 'person-select';
      case 'file':
        return 'file';
      default:
        return 'text';
    }
  };
  
  // Handle variable substitution in prompts
  const handlePromptChange = (newValue: string) => {
    // If this is a prompt field and it contains variables, preserve them
    onChange(newValue);
  };
  
  // Get the appropriate onChange handler
  const getOnChange = () => {
    if (field.type === 'string' && (field.name.includes('prompt') || field.name.includes('Prompt'))) {
      return handlePromptChange;
    }
    return onChange;
  };
  
  // Build options for select fields
  const getOptions = () => {
    if (field.options) {
      return field.options.map((opt: any) => ({
        value: typeof opt === 'string' ? opt : opt.value,
        label: typeof opt === 'string' ? opt : opt.label
      }));
    }
    return [];
  };
  
  // Get persons for person-select fields
  const getPersons = () => {
    return Object.values(persons).map(p => ({
      id: p.id,
      name: p.label || 'Unknown'
    }));
  };
  
  return (
    <UnifiedFormField
      type={getFieldType()}
      name={field.name}
      label={field.label}
      value={value}
      onChange={getOnChange()}
      placeholder={field.placeholder}
      options={getOptions()}
      persons={getPersons()}
      required={field.isRequired}
      min={field.min}
      max={field.max}
      layout={layout}
      className={className}
      helperText={field.helperText}
      acceptedFileTypes={field.acceptedFileTypes}
      customProps={{
        ...field.customProps,
        // Add any field-specific props here
      }}
    />
  );
};

/**
 * Render multiple fields with a unified renderer
 */
export const UnifiedFieldsRenderer: React.FC<{
  fields: PropertyFieldConfig[];
  values: Record<string, any>;
  onChange: (name: string, value: any) => void;
  layout?: 'inline' | 'vertical';
  className?: string;
}> = ({ fields, values, onChange, layout = 'inline', className }) => {
  return (
    <div className={`space-y-4 ${className || ''}`}>
      {fields.map((field) => (
        <UnifiedFieldRenderer
          key={field.name}
          field={field}
          value={values[field.name]}
          onChange={(value) => onChange(field.name, value)}
          layout={layout}
        />
      ))}
    </div>
  );
};