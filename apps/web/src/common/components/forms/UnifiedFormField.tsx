import React from 'react';
import { Input } from '../Input';
import { Select } from '../Select';
import { Switch } from '../Switch';
import { FileUploadButton } from '../common/FileUploadButton';

export interface UnifiedFormFieldProps {
  type: 'text' | 'select' | 'textarea' | 'checkbox' | 'number' | 'file' | 'person-select' | 'iteration-count';
  name: string;
  label: string;
  value: any;
  onChange: (value: any) => void;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  className?: string;
  disabled?: boolean;
  required?: boolean;
  min?: number;
  max?: number;
  layout?: 'inline' | 'vertical';
  error?: string;
  helperText?: string;
  persons?: Array<{ id: string; name: string }>;
  acceptedFileTypes?: string;
  customProps?: Record<string, any>;
}

/**
 * Unified form field component that renders the appropriate field type
 * based on the 'type' prop. This consolidates all form field rendering logic.
 */
export const UnifiedFormField: React.FC<UnifiedFormFieldProps> = ({
  type,
  name,
  label,
  value,
  onChange,
  placeholder,
  options = [],
  className = '',
  disabled = false,
  required = false,
  min,
  max,
  layout = 'inline',
  error,
  helperText,
  persons = [],
  acceptedFileTypes,
  customProps = {}
}) => {
  const fieldId = `field-${name}`;
  
  const renderField = () => {
    switch (type) {
      case 'text':
        return (
          <Input
            id={fieldId}
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full"
            {...customProps}
          />
        );
        
      case 'number':
      case 'iteration-count':
        return (
          <Input
            id={fieldId}
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
            placeholder={placeholder}
            disabled={disabled}
            min={min}
            max={max}
            className="w-full"
            {...customProps}
          />
        );
        
      case 'textarea':
        return (
          <textarea
            id={fieldId}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            rows={4}
            className="w-full px-3 py-2 text-sm bg-background-secondary border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            {...customProps}
          />
        );
        
      case 'select':
        return (
          <Select
            value={value || ''}
            onChange={onChange}
            disabled={disabled}
            className="w-full"
            {...customProps}
          >
            {placeholder && <option value="">
              {placeholder}
            </option>}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        );
        
      case 'person-select':
        return (
          <Select
            value={value || ''}
            onChange={onChange}
            disabled={disabled}
            className="w-full"
            {...customProps}
          >
            <option value="">
              Select person...
            </option>
            {persons.map((person) => (
              <option key={person.id} value={person.id}>
                {person.name}
              </option>
            ))}
          </Select>
        );
        
      case 'checkbox':
        return (
          <Switch
            id={fieldId}
            checked={!!value}
            onChange={onChange}
            disabled={disabled}
            {...customProps}
          />
        );
        
      case 'file':
        return (
          <FileUploadButton
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                const reader = new FileReader();
                reader.onload = (e) => onChange(e.target?.result as string);
                reader.readAsText(file);
              }
            }}
            accept={acceptedFileTypes}
            disabled={disabled}
            className="w-full"
            {...customProps}
          >
            Select File
          </FileUploadButton>
        );
        
      default:
        return null;
    }
  };
  
  const fieldElement = renderField();
  
  if (layout === 'vertical') {
    return (
      <div className={`space-y-2 ${className}`}>
        <label htmlFor={fieldId} className="block text-sm font-medium text-text-primary">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {fieldElement}
        {helperText && <p className="text-xs text-text-tertiary">{helperText}</p>}
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    );
  }
  
  // Inline layout (default)
  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <label htmlFor={fieldId} className="text-sm font-medium text-text-primary min-w-[120px]">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <div className="flex-1">
        {fieldElement}
        {helperText && <p className="text-xs text-text-tertiary mt-1">{helperText}</p>}
        {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
      </div>
    </div>
  );
};

// Factory function for creating form fields based on configuration
export const createFormField = (config: UnifiedFormFieldProps) => {
  return <UnifiedFormField {...config} />;
};