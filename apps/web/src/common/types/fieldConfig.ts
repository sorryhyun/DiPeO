/**
 * Field configuration for node properties
 */
export interface FieldConfig {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'string' | 'boolean' | 'person' | 'file';
  placeholder?: string;
  isRequired?: boolean;
  required?: boolean;
  options?: { value: string; label: string }[];
  rows?: number;
  hint?: string;
  helperText?: string;
  multiline?: boolean;
  min?: number;
  max?: number;
  acceptedFileTypes?: string;
  customProps?: Record<string, any>;
  disabled?: boolean;
}

/**
 * Property field configuration used in unified system
 */
export type PropertyFieldConfig = FieldConfig;