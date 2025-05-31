import React, { useMemo, useState } from 'react';
import {
  Input, Label, Select, SelectItem, Textarea, Spinner, Switch
} from '../../../../shared/components';
import { FileUploadButton } from '../../../../shared/components/common/FileUploadButton';
import { FormFieldProps } from '@/shared/types';
import { usePersons } from '@/shared/hooks/useStoreSelectors';

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

interface CheckboxFieldProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  id?: string;
}

export const CheckboxField: React.FC<CheckboxFieldProps> = ({ label, checked, onChange, id }) => (
  <div className="flex items-center space-x-2">
    <Switch
      id={id}
      checked={checked}
      onChange={onChange}
    />
    <Label htmlFor={id} className="text-sm font-medium cursor-pointer">{label}</Label>
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

// Specialized Field Components
interface PersonSelectionFieldProps {
  value: string;
  onChange: (personId: string) => void;
  className?: string;
  required?: boolean;
  placeholder?: string;
}

export const PersonSelectionField: React.FC<PersonSelectionFieldProps> = ({
  value,
  onChange,
  className,
  required = false,
  placeholder
}) => {
  const { persons } = usePersons();
  const personOptions = useMemo(
    () => persons.map(p => ({ value: p.id, label: p.label })),
    [persons]
  );

  return (
    <InlineSelectField
      label="Person"
      value={value}
      onChange={(v) => onChange(v || '')}
      options={personOptions}
      placeholder={placeholder || (required ? "Select person" : "None")}
      className={className}
    />
  );
};

interface LabelPersonRowProps {
  labelValue: string;
  onLabelChange: (value: string) => void;
  personValue: string;
  onPersonChange: (personId: string) => void;
  labelPlaceholder?: string;
  personPlaceholder?: string;
}

export const LabelPersonRow: React.FC<LabelPersonRowProps> = ({
  labelValue,
  onLabelChange,
  personValue,
  onPersonChange,
  labelPlaceholder = "Enter label",
  personPlaceholder
}) => (
  <FormRow>
    <InlineTextField
      label="Label"
      value={labelValue}
      onChange={onLabelChange}
      placeholder={labelPlaceholder}
      className="flex-1"
    />
    <PersonSelectionField
      value={personValue}
      onChange={onPersonChange}
      placeholder={personPlaceholder}
      className="flex-1"
    />
  </FormRow>
);

interface IterationCountFieldProps {
  value: number;
  onChange: (count: number) => void;
  className?: string;
  min?: number;
  max?: number;
  label?: string;
}

export const IterationCountField: React.FC<IterationCountFieldProps> = ({
  value,
  onChange,
  className = "w-24",
  min = 1,
  max = 100,
  label = "Max Iter"
}) => (
  <InlineTextField
    label={label}
    value={String(value || min)}
    onChange={(v) => {
      const num = parseInt(v) || min;
      onChange(Math.min(Math.max(num, min), max));
    }}
    placeholder={String(min)}
    className={className}
  />
);

interface VariableDetectionTextAreaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  detectedVariables?: string[];
  placeholder?: string;
  rows?: number;
}

export const VariableDetectionTextArea: React.FC<VariableDetectionTextAreaProps> = ({
  label,
  value,
  onChange,
  detectedVariables,
  placeholder,
  rows = 4
}) => {
  const hint = useMemo(() => {
    if (!detectedVariables?.length) return undefined;
    return `Detected variables: ${detectedVariables.map(v => `{{${v}}}`).join(', ')}`;
  }, [detectedVariables]);

  return (
    <TextAreaField
      label={label}
      value={value}
      onChange={onChange}
      rows={rows}
      placeholder={placeholder}
      hint={hint}
    />
  );
};

interface RadioGroupFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  id?: string;
}

export const RadioGroupField: React.FC<RadioGroupFieldProps> = ({
  label,
  value,
  onChange,
  options,
  id
}) => (
  <FormField label={label} id={id}>
    <div className="space-y-2" role="radiogroup" aria-labelledby={id}>
      {options.map((option) => (
        <div key={option.value} className="flex items-center space-x-2">
          <input
            type="radio"
            id={`${id || label}-${option.value}`}
            value={option.value}
            checked={value === option.value}
            onChange={(e) => onChange(e.target.value)}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
          />
          <Label 
            htmlFor={`${id || label}-${option.value}`}
            className="text-sm font-medium cursor-pointer"
          >
            {option.label}
          </Label>
        </div>
      ))}
    </div>
  </FormField>
);

interface FileUploadFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onFileUpload: (file: File) => Promise<void>;
  accept?: string;
  loading?: boolean;
  placeholder?: string;
  id?: string;
}

export const FileUploadField: React.FC<FileUploadFieldProps> = ({
  label,
  value,
  onChange,
  onFileUpload,
  accept = ".txt,.docx,.doc,.pdf,.csv,.json",
  loading = false,
  placeholder = "Enter file path or upload below",
  id
}) => {
  const [localLoading, setLocalLoading] = useState(false);
  const isLoading = loading || localLoading;

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLocalLoading(true);
    try {
      await onFileUpload(file);
    } finally {
      setLocalLoading(false);
    }
  };

  return (
    <FormField label={label} id={id}>
      <div className="space-y-2">
        <Input
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={isLoading}
        />
        
        <div className="flex items-center gap-2">
          <FileUploadButton
            accept={accept}
            onChange={handleFileUpload}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            {isLoading ? "Uploading..." : "Upload File"}
          </FileUploadButton>
          
          {isLoading && (
            <div className="flex items-center text-sm text-gray-600">
              <Spinner size="sm" className="mr-2" />
              <span>Uploading...</span>
            </div>
          )}
        </div>
      </div>
    </FormField>
  );
};