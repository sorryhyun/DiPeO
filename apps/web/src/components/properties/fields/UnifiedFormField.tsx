import React, { useState, useMemo } from 'react';
import { Input, Select, Switch, Spinner, FileUploadButton } from '../../ui';
import { 
  FULL_WIDTH, SPACE_Y_2, TEXTAREA_CLASSES, LABEL_TEXT, 
  ERROR_TEXT, ERROR_TEXT_MT, HELPER_TEXT, HELPER_TEXT_MT, 
  REQUIRED_ASTERISK, FLEX_CENTER_GAP 
} from '../styles.constants';
import { readFileAsText } from '@/utils/file';

export type FieldValue = string | number | boolean | null | undefined;

export interface UnifiedFormFieldProps {
  type: 'text' | 'select' | 'textarea' | 'checkbox' | 'number' | 'file' | 'person-select' | 'iteration-count' | 'variable-textarea';
  name: string;
  label: string;
  value: FieldValue;
  onChange: (value: FieldValue) => void;
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
  customProps?: Record<string, unknown>;
  rows?: number;
  hint?: string;
  detectedVariables?: string[];
  onFileUpload?: (file: File) => Promise<void>;
  isLoading?: boolean;
}

type WidgetProps = Omit<UnifiedFormFieldProps, 'type' | 'name' | 'label' | 'layout' | 'error' | 'helperText'> & {
  fieldId: string;
  isLoadingState: boolean;
  setLocalLoading: (loading: boolean) => void;
};

// Widget lookup table for field types
const widgets: Record<UnifiedFormFieldProps['type'], (props: WidgetProps) => React.JSX.Element | null> = {
  text: (p) => (
    <Input
      id={p.fieldId}
      type="text"
      value={String(p.value || '')}
      onChange={(e) => p.onChange(e.target.value)}
      placeholder={p.placeholder}
      disabled={p.disabled}
      className={FULL_WIDTH}
      {...p.customProps}
    />
  ),
  
  number: (p) => (
    <Input
      id={p.fieldId}
      type="number"
      value={String(p.value || '')}
      onChange={(e) => p.onChange(e.target.value ? Number(e.target.value) : null)}
      placeholder={p.placeholder}
      disabled={p.disabled}
      min={p.min}
      max={p.max}
      className={FULL_WIDTH}
      {...p.customProps}
    />
  ),
  
  'iteration-count': (p) => widgets.number(p),
  
  textarea: (p) => (
    <textarea
      id={p.fieldId}
      value={String(p.value || '')}
      onChange={(e) => p.onChange(e.target.value)}
      placeholder={p.placeholder}
      disabled={p.disabled}
      rows={p.rows}
      className={TEXTAREA_CLASSES}
      {...p.customProps}
    />
  ),
  
  'variable-textarea': (p) => widgets.textarea(p),
  
  select: (p) => (
    <Select
      value={String(p.value || '')}
      onValueChange={p.onChange}
      disabled={p.disabled}
      className={FULL_WIDTH}
      {...p.customProps}
    >
      {p.placeholder && <option value="">{p.placeholder}</option>}
      {p.options?.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </Select>
  ),
  
  'person-select': (p) => (
    <Select
      value={String(p.value || '')}
      onValueChange={p.onChange}
      disabled={p.disabled}
      className={FULL_WIDTH}
      {...p.customProps}
    >
      <option value="">Select person...</option>
      {p.persons?.map((person) => (
        <option key={person.id} value={person.id}>
          {person.name}
        </option>
      ))}
    </Select>
  ),
  
  checkbox: (p) => (
    <Switch
      id={p.fieldId}
      checked={!!p.value}
      onChange={p.onChange}
      disabled={p.disabled}
      {...p.customProps}
    />
  ),
  
  file: (p) => {
    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      if (p.onFileUpload) {
        p.setLocalLoading(true);
        try {
          await p.onFileUpload(file);
        } finally {
          p.setLocalLoading(false);
        }
      } else {
        // Default behavior: read as text
        try {
          const content = await readFileAsText(file);
          p.onChange(content);
        } catch (error) {
          console.error('Error reading file:', error);
        }
      }
    };

    return (
      <div className={SPACE_Y_2}>
        <Input
          id={p.fieldId}
          value={String(p.value || '')}
          onChange={(e) => p.onChange(e.target.value)}
          placeholder={p.placeholder || "Enter file path or upload below"}
          disabled={p.isLoadingState}
          className={FULL_WIDTH}
        />
        
        <div className={FLEX_CENTER_GAP}>
          <FileUploadButton
            accept={p.acceptedFileTypes || ".txt,.docx,.doc,.pdf,.csv,.json"}
            onChange={handleFileUpload}
            disabled={p.isLoadingState}
            variant="outline"
            size="sm"
            {...p.customProps}
          >
            {p.isLoadingState ? "Uploading..." : "Upload File"}
          </FileUploadButton>
          
          {p.isLoadingState && (
            <div className="flex items-center text-sm text-gray-600">
              <Spinner size="sm" className="mr-2" />
              <span>Uploading...</span>
            </div>
          )}
        </div>
      </div>
    );
  }
};

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
  customProps = {},
  rows = 4,
  hint,
  detectedVariables,
  onFileUpload,
  isLoading = false
}) => {
  const fieldId = `field-${name}`;
  const [localLoading, setLocalLoading] = useState(false);
  const isLoadingState = isLoading || localLoading;
  
  // Memoize variable detection hint
  const variableHint = useMemo(() => {
    if (!detectedVariables?.length) return hint;
    const variableText = `Detected variables: ${detectedVariables.map(v => `{{${v}}}`).join(', ')}`;
    return hint ? `${hint}\n${variableText}` : variableText;
  }, [detectedVariables, hint]);
  
  // Create widget props
  const widgetProps: WidgetProps = {
    value,
    onChange,
    placeholder,
    options,
    disabled,
    min,
    max,
    persons,
    acceptedFileTypes,
    customProps,
    rows,
    hint,
    detectedVariables,
    onFileUpload,
    isLoading,
    fieldId,
    isLoadingState,
    setLocalLoading
  };
  
  const fieldElement = widgets[type]?.(widgetProps) ?? null;
  
  if (layout === 'vertical') {
    return (
      <div className={`${SPACE_Y_2} ${className}`}>
        <label htmlFor={fieldId} className={`block ${LABEL_TEXT}`}>
          {label}
          {required && <span className={REQUIRED_ASTERISK}>*</span>}
        </label>
        {fieldElement}
        {(helperText || variableHint) && <p className={HELPER_TEXT}>{variableHint || helperText}</p>}
        {error && <p className={ERROR_TEXT}>{error}</p>}
      </div>
    );
  }
  
  // Inline layout (default)
  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <label htmlFor={fieldId} className={`${LABEL_TEXT} min-w-[120px]`}>
        {label}
        {required && <span className={REQUIRED_ASTERISK}>*</span>}
      </label>
      <div className="flex-1">
        {fieldElement}
        {(helperText || variableHint) && <p className={HELPER_TEXT_MT}>{variableHint || helperText}</p>}
        {error && <p className={ERROR_TEXT_MT}>{error}</p>}
      </div>
    </div>
  );
};