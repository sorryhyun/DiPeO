import React from 'react';
import {
  Input, Label, Select, SelectItem, Textarea, Spinner
} from '../../../../shared/components';
import { FormFieldProps } from '@/shared/types';

export const FormField: React.FC<FormFieldProps> = ({ label, id, children, className = "space-y-1" }) => (
  <div className={className}>
    <Label htmlFor={id} className="text-xs font-medium">{label}</Label>
    {children}
  </div>
);

interface FormLayoutProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3;
}

export const FormGrid: React.FC<FormLayoutProps> = ({ children, columns = 1 }) => {
  const gridClass = columns === 3 ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3" :
                    columns === 2 ? "grid-cols-1 sm:grid-cols-2" :
                    "grid-cols-1";
  return <div className={`grid ${gridClass} gap-3`}>{children}</div>;
};

export const Form: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <form className="space-y-3">{children}</form>
);

// Inline form field component for horizontal layouts
export const InlineFormField: React.FC<FormFieldProps> = ({ label, id, children, className = "flex items-center gap-2" }) => (
  <div className={className}>
    <Label htmlFor={id} className="text-xs font-medium whitespace-nowrap">{label}</Label>
    <div className="flex-1">{children}</div>
  </div>
);

// Horizontal form row for inline fields
export const FormRow: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = "flex flex-wrap gap-3" }) => (
  <div className={className}>{children}</div>
);

interface TextFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  id?: string;
}

export const TextField: React.FC<TextFieldProps> = ({ label, value, onChange, placeholder, id }) => (
  <FormField label={label} id={id}>
    <Input
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  </FormField>
);

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
  id?: string;
  disabled?: boolean;
  loading?: boolean;
  error?: string | null;
}

export const SelectField: React.FC<SelectFieldProps> = ({
  label, value, onChange, options, placeholder = "Select an option", id, disabled, loading, error
}) => (
  <FormField label={label} id={id}>
    {loading ? (
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
        disabled={disabled}
      >
        <SelectItem value="">{placeholder}</SelectItem>
        {options.map(opt => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </Select>
    )}
  </FormField>
);

interface TextAreaFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  id?: string;
  hint?: string;
}

export const TextAreaField: React.FC<TextAreaFieldProps> = ({
  label, value, onChange, placeholder, rows = 4, id, hint
}) => (
  <FormField label={label} id={id}>
    <Textarea
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
    />
    {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
  </FormField>
);

// Inline versions of field components
export const InlineTextField: React.FC<TextFieldProps & { className?: string }> = ({ label, value, onChange, placeholder, id, className }) => (
  <InlineFormField label={label} id={id} className={className}>
    <Input
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="min-w-0"
    />
  </InlineFormField>
);

export const InlineSelectField: React.FC<SelectFieldProps & { className?: string }> = ({
  label, value, onChange, options, placeholder = "Select", id, disabled, loading, error, className
}) => (
  <InlineFormField label={label} id={id} className={className}>
    {loading ? (
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
        disabled={disabled}
        className="min-w-0"
      >
        <SelectItem value="">{placeholder}</SelectItem>
        {options.map(opt => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </Select>
    )}
  </InlineFormField>
);