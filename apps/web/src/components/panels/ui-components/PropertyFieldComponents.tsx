import React, { useMemo, useState } from 'react';
import { Input, Spinner, Select } from '@/common/components';
import { FileUploadButton } from '@/common';
import { usePersons } from '@/state/hooks/useStoreSelectors';

// Specialized Field Components for Property Panels

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
    <div className="flex items-center gap-2">
      <label className="text-xs font-medium whitespace-nowrap">Person</label>
      <Select
        value={value}
        onValueChange={(v) => onChange(v || '')}
        disabled={disabled}
      >
        <Select.Trigger className={className}>
          <Select.Value placeholder={placeholder || (required ? "Select person" : "None")} />
        </Select.Trigger>
        <Select.Content>
          {personOptions.map(opt => (
            <Select.Item key={opt.value} value={opt.value}>
              {opt.label}
            </Select.Item>
          ))}
        </Select.Content>
      </Select>
    </div>
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
  <div className="flex flex-wrap gap-3">
    <div className="flex items-center gap-2 flex-1">
      <label className="text-xs font-medium whitespace-nowrap">Label</label>
      <Input
        value={labelValue}
        onChange={(e) => onLabelChange(e.target.value)}
        placeholder={labelPlaceholder}
        disabled={disabled}
      />
    </div>
    <PersonSelectionField
      value={personValue}
      onChange={onPersonChange}
      placeholder={personPlaceholder}
      className="flex-1"
      disabled={disabled}
    />
  </div>
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
  <div className="flex items-center gap-2">
    <label className="text-xs font-medium whitespace-nowrap">{label}</label>
    <Input
      type="number"
      value={String(value || min)}
      onChange={(e) => {
        const num = parseInt(e.target.value) || min;
        onChange(Math.min(Math.max(num, min), max));
      }}
      placeholder={String(min)}
      className={className}
      disabled={disabled}
      min={min}
      max={max}
    />
  </div>
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
    <div className="space-y-1">
      <label className="text-xs font-medium">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
        className="flex w-full rounded-md border border-slate-300 bg-transparent py-1.5 px-2.5 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
      />
      {hint && <p className="text-xs text-gray-600">{hint}</p>}
    </div>
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
    <div className="space-y-1">
      <label htmlFor={id} className="text-xs font-medium">{label}</label>
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
    </div>
  );
};