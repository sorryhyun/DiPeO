/**
 * Form field validation and utility types
 */

/**
 * Field validation result interface
 */
export interface FieldValidationResult {
  isValid: boolean;
  error?: string;
  warning?: string;
}

/**
 * Property field types for form rendering
 */
export type PropertyFieldType = 
  | 'text'
  | 'number'
  | 'boolean'
  | 'select'
  | 'textarea'
  | 'json'
  | 'array'
  | 'object'
  | 'email'
  | 'url';

/**
 * Field configuration for dynamic forms
 */
export interface FormFieldConfig {
  key: string;
  type: PropertyFieldType;
  label?: string;
  required?: boolean;
  placeholder?: string;
  min?: number;
  max?: number;
  options?: Array<{ value: string; label: string }>;
  validation?: (value: unknown) => FieldValidationResult;
}