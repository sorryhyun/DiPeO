import React from 'react';
import { Input, Select, Spinner, Switch } from '../index';
import { FormFieldProps } from '../../../types';

export const FormField: React.FC<FormFieldProps> = ({ label, id, children, className = "space-y-1" }) => (
  <div className={className}>
    <label htmlFor={id} className="text-xs font-medium">{label}</label>
    {children}
  </div>
);

export const Form: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <form className="space-y-3">{children}</form>
);

// Inline form field component for horizontal layouts
export const InlineFormField: React.FC<FormFieldProps> = ({ label, id, children, className = "flex items-center gap-2" }) => (
  <div className={className}>
    <label htmlFor={id} className="text-xs font-medium whitespace-nowrap">{label}</label>
    <div className="flex-1">{children}</div>
  </div>
);

// Horizontal form row for inline fields
export const FormRow: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = "flex flex-wrap gap-3" }) => (
  <div className={className}>{children}</div>
);


interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
  id?: string;
  isDisabled?: boolean;
  isLoading?: boolean;
  error?: string | null;
}


interface TextAreaFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  id?: string;
  hint?: string;
  disabled?: boolean;
}

export const TextAreaField: React.FC<TextAreaFieldProps> = ({
  label, value, onChange, placeholder, rows = 4, id, hint, disabled
}) => (
  <FormField label={label} id={id}>
    <textarea
      id={id}
      value={value}
      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
      disabled={disabled}
      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
    />
    {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
  </FormField>
);

// Inline versions of field components
interface InlineTextFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  id?: string;
  disabled?: boolean;
  className?: string;
}

export const InlineTextField: React.FC<InlineTextFieldProps> = ({ label, value, onChange, placeholder, id, className, disabled }) => (
  <InlineFormField label={label} id={id} className={className}>
    <Input
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="min-w-0"
      disabled={disabled}
    />
  </InlineFormField>
);

export const InlineSelectField: React.FC<SelectFieldProps & { className?: string }> = ({
  label, value, onChange, options, placeholder = "Select", id, isDisabled, isLoading, error, className
}) => (
  <InlineFormField label={label} id={id} className={className}>
    {isLoading ? (
      <div className="flex items-center space-x-2">
        <Spinner size="sm" />
        <span className="text-sm">Loading...</span>
      </div>
    ) : error ? (
      <p className="text-xs text-red-500">Error: {error}</p>
    ) : (
      <Select
        id={id}
        value={value}
        onValueChange={onChange}
        disabled={isDisabled}
        className="min-w-0"
      >
        <option value="">{placeholder}</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </Select>
    )}
  </InlineFormField>
);

interface CheckboxFieldProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  id?: string;
  disabled?: boolean;
}

export const CheckboxField: React.FC<CheckboxFieldProps> = ({ label, checked, onChange, id, disabled }) => (
  <div className="flex items-center space-x-2">
    <Switch
      id={id}
      checked={checked}
      onChange={onChange}
      disabled={disabled}
    />
    <label htmlFor={id} className="text-sm font-medium cursor-pointer">{label}</label>
  </div>
);

// Layout Components
interface TwoColumnLayoutProps {
  leftColumn: React.ReactNode;
  rightColumn: React.ReactNode;
}

export const TwoColumnPanelLayout: React.FC<TwoColumnLayoutProps> = ({ 
  leftColumn, 
  rightColumn 
}) => (
  <div className="grid grid-cols-2 gap-4">
    <div className="space-y-4">{leftColumn}</div>
    <div className="space-y-4">{rightColumn}</div>
  </div>
);

export const SingleColumnPanelLayout: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => (
  <div className="space-y-4">{children}</div>
);

