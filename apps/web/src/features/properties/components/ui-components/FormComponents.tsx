import React, { useMemo, useState } from 'react';
import { Input, Spinner } from '@/shared/components';
import { FileUploadButton } from '@/shared';
import { usePersons } from '@/global/hooks/useStoreSelectors';
import {
  FormField,
  FormRow,
  InlineSelectField,
  InlineTextField,
  TextAreaField
} from '@/shared/components/forms';

// Specialized Field Components

interface PersonSelectionFieldProps {
  value: string;
  onChange: (personId: string) => void;
  className?: string;
  required?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export const PersonSelectionField: React.FC<PersonSelectionFieldProps> = ({
  value,
  onChange,
  className,
  required = false,
  placeholder,
  disabled
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
      isDisabled={disabled}
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
  disabled?: boolean;
}

export const LabelPersonRow: React.FC<LabelPersonRowProps> = ({
  labelValue,
  onLabelChange,
  personValue,
  onPersonChange,
  labelPlaceholder = "Enter label",
  personPlaceholder,
  disabled
}) => (
  <FormRow>
    <InlineTextField
      label="Label"
      value={labelValue}
      onChange={onLabelChange}
      placeholder={labelPlaceholder}
      className="flex-1"
      disabled={disabled}
    />
    <PersonSelectionField
      value={personValue}
      onChange={onPersonChange}
      placeholder={personPlaceholder}
      className="flex-1"
      disabled={disabled}
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
  disabled?: boolean;
}

export const IterationCountField: React.FC<IterationCountFieldProps> = ({
  value,
  onChange,
  className = "w-24",
  min = 1,
  max = 100,
  label = "Max Iter",
  disabled
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
    disabled={disabled}
  />
);

interface VariableDetectionTextAreaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  detectedVariables?: string[];
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
}

export const VariableDetectionTextArea: React.FC<VariableDetectionTextAreaProps> = ({
  label,
  value,
  onChange,
  detectedVariables,
  placeholder,
  rows = 4,
  disabled
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
      disabled={disabled}
    />
  );
};

interface FileUploadFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onFileUpload: (file: File) => Promise<void>;
  accept?: string;
  isLoading?: boolean;
  placeholder?: string;
  id?: string;
}

export const FileUploadField: React.FC<FileUploadFieldProps> = ({
  label,
  value,
  onChange,
  onFileUpload,
  accept = ".txt,.docx,.doc,.pdf,.csv,.json",
  isLoading = false,
  placeholder = "Enter file path or upload below",
  id
}) => {
  const [localLoading, setLocalLoading] = useState(false);
  const isLoadingState = isLoading || localLoading;

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
          disabled={isLoadingState}
        />
        
        <div className="flex items-center gap-2">
          <FileUploadButton
            accept={accept}
            onChange={handleFileUpload}
            disabled={isLoadingState}
            variant="outline"
            size="sm"
          >
            {isLoadingState ? "Uploading..." : "Upload File"}
          </FileUploadButton>
          
          {isLoadingState && (
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

// Re-export commonly used generic components for convenience
export {
  FormField,
  Form,
  FormRow,
  InlineFormField,
  TextAreaField,
  InlineTextField,
  InlineSelectField,
  CheckboxField,
  TwoColumnPanelLayout,
  SingleColumnPanelLayout
} from '@/shared/components/forms';