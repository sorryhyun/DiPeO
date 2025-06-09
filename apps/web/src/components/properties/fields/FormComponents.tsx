import React from 'react';
import { Input, Select, Spinner, Switch } from '../../ui';

interface FormFieldProps {
  label: string;
  id: string;
  children: React.ReactNode;
  className?: string;
}
import { 
  LABEL_TEXT_SMALL, MIN_WIDTH_0, INPUT_BASE, SPACE_Y_4, 
  ERROR_TEXT, FLEX_CENTER_SPACE, LABEL_TEXT 
} from '../styles.constants';

export const FormField: React.FC<FormFieldProps> = ({ label, id, children, className = "space-y-1" }) => (
  <div className={className}>
    <label htmlFor={id} className={LABEL_TEXT_SMALL}>{label}</label>
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
  <FormField label={label} id={id || ''}>
    <textarea
      id={id}
      value={value || ''}
      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
      disabled={disabled}
      className={INPUT_BASE}
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
  <InlineFormField label={label} id={id || ''} className={className}>
    <Input
      id={id}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={MIN_WIDTH_0}
      disabled={disabled}
    />
  </InlineFormField>
);

export const InlineSelectField: React.FC<SelectFieldProps & { className?: string }> = ({
  label, value, onChange, options, placeholder = "Select", id, isDisabled, isLoading, error, className
}) => (
  <InlineFormField label={label} id={id || ''} className={className}>
    {isLoading ? (
      <div className={FLEX_CENTER_SPACE}>
        <Spinner size="sm" />
        <span className="text-sm">Loading...</span>
      </div>
    ) : error ? (
      <p className={ERROR_TEXT}>Error: {error}</p>
    ) : (
      <Select
        id={id}
        value={value}
        onValueChange={onChange}
        disabled={isDisabled}
        className={MIN_WIDTH_0}
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
  <div className={FLEX_CENTER_SPACE}>
    <Switch
      id={id}
      checked={checked}
      onChange={onChange}
      disabled={disabled}
    />
    <label htmlFor={id} className={`${LABEL_TEXT} cursor-pointer`}>{label}</label>
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
    <div className={SPACE_Y_4}>{leftColumn}</div>
    <div className={SPACE_Y_4}>{rightColumn}</div>
  </div>
);

export const SingleColumnPanelLayout: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => (
  <div className={SPACE_Y_4}>{children}</div>
);

