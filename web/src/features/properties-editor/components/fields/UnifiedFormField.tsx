import React, { useState, useMemo } from 'react';
import { Input, Select, Switch, Spinner, FileUploadButton } from '@/shared/components/ui';
import { 
  FULL_WIDTH, SPACE_Y_2, TEXTAREA_CLASSES, LABEL_TEXT, 
  ERROR_TEXT, ERROR_TEXT_MT, HELPER_TEXT, HELPER_TEXT_MT, 
  REQUIRED_ASTERISK, FLEX_CENTER_GAP 
} from '../styles.constants';
import { readFileAsText } from '@/shared/utils/file';
import { FIELD_TYPES } from '@/core/types/panel';

export type FieldValue = string | number | boolean | null | undefined;

// Map UnifiedFormField types to base field types
export type UnifiedFieldType = 
  | typeof FIELD_TYPES.TEXT
  | typeof FIELD_TYPES.SELECT
  | typeof FIELD_TYPES.TEXTAREA
  | typeof FIELD_TYPES.BOOLEAN
  | typeof FIELD_TYPES.NUMBER
  | typeof FIELD_TYPES.PERSON_SELECT
  | typeof FIELD_TYPES.MAX_ITERATION
  | typeof FIELD_TYPES.VARIABLE_TEXTAREA
  | 'file'; // File is UI-specific, not in base types

// Legacy type mapping for backward compatibility
const LEGACY_TYPE_MAP: Record<string, UnifiedFieldType> = {
  'checkbox': FIELD_TYPES.BOOLEAN,
  'iteration-count': FIELD_TYPES.MAX_ITERATION,
  'person-select': FIELD_TYPES.PERSON_SELECT,
  'variable-textarea': FIELD_TYPES.VARIABLE_TEXTAREA,
};

export interface UnifiedFormFieldProps {
  type: UnifiedFieldType;
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
  persons?: Array<{ id: string; label: string }>;
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

// Normalize legacy type names
function normalizeFieldType(type: string): UnifiedFieldType {
  return (LEGACY_TYPE_MAP[type] || type) as UnifiedFieldType;
}

// Widget lookup table for field types
const widgets: Record<UnifiedFieldType, (props: WidgetProps) => React.JSX.Element | null> = {
  [FIELD_TYPES.TEXT]: (p) => (
    <Input
      id={p.fieldId}
      type="text"
      value={String(p.value || '')}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => p.onChange(e.target.value)}
      placeholder={p.placeholder}
      disabled={p.disabled}
      className={FULL_WIDTH}
      {...p.customProps}
    />
  ),
  
  [FIELD_TYPES.NUMBER]: (p) => (
    <Input
      id={p.fieldId}
      type="number"
      value={String(p.value || '')}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => p.onChange(e.target.value ? Number(e.target.value) : null)}
      placeholder={p.placeholder}
      disabled={p.disabled}
      min={p.min}
      max={p.max}
      className={FULL_WIDTH}
      {...p.customProps}
    />
  ),
  
  [FIELD_TYPES.MAX_ITERATION]: (p) => widgets[FIELD_TYPES.NUMBER](p),
  
  [FIELD_TYPES.TEXTAREA]: (p) => (
    <textarea
      id={p.fieldId}
      value={String(p.value || '')}
      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => p.onChange(e.target.value)}
      placeholder={p.placeholder}
      disabled={p.disabled}
      rows={p.rows}
      className={TEXTAREA_CLASSES}
      {...p.customProps}
    />
  ),
  
  [FIELD_TYPES.VARIABLE_TEXTAREA]: (p) => widgets[FIELD_TYPES.TEXTAREA](p),
  
  [FIELD_TYPES.SELECT]: (p) => (
    <Select
      id={p.fieldId}
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
  
  [FIELD_TYPES.PERSON_SELECT]: (p) => (
    <Select
      id={p.fieldId}
      value={String(p.value || '')}
      onValueChange={p.onChange}
      disabled={p.disabled}
      className={FULL_WIDTH}
      {...p.customProps}
    >
      <option value="">Select person...</option>
      {p.persons?.map((person) => (
        <option key={person.id} value={person.id}>
          {person.label}
        </option>
      ))}
    </Select>
  ),
  
  [FIELD_TYPES.BOOLEAN]: (p) => (
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
  
  // Normalize field type for lookup
  const normalizedType = normalizeFieldType(type);
  const fieldElement = widgets[normalizedType]?.(widgetProps) ?? null;
  
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