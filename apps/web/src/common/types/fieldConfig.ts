/**
 * Base field configuration for node properties
 */
export interface FieldConfig {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox';
  placeholder?: string;
  isRequired?: boolean;
  options?: { value: string; label: string }[];
  rows?: number;
  hint?: string;
}

/**
 * Extended field configuration that supports all field types used in the application
 */
export interface FieldConfig extends Omit<FieldConfig, 'type'> {
  type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'string' | 'boolean' | 'person' | 'file';
  multiline?: boolean;
  min?: number;
  max?: number;
  helperText?: string;
  acceptedFileTypes?: string;
  customProps?: Record<string, any>;
  disabled?: boolean;
  required?: boolean;
}

/**
 * Property field configuration used in unified system
 */
export type PropertyFieldConfig = FieldConfig;