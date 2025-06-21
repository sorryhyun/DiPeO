/**
 * Form field validation and utility types
 */

import { FIELD_TYPES, type ValidationResult, type FieldType } from '@/core/types/panel';

/**
 * Property field types for form rendering
 * Extended field types that include data types not in base panel fields
 */
export type PropertyFieldType = 
  | FieldType
  | 'json'
  | 'array'
  | 'object'
  | 'email'
  | 'url';

/**
 * Map property field types to base field types
 */
export const PROPERTY_TO_BASE_FIELD_TYPE: Record<string, FieldType> = {
  'text': FIELD_TYPES.TEXT,
  'number': FIELD_TYPES.NUMBER,
  'boolean': FIELD_TYPES.BOOLEAN,
  'select': FIELD_TYPES.SELECT,
  'textarea': FIELD_TYPES.TEXTAREA,
  'json': FIELD_TYPES.TEXTAREA,
  'array': FIELD_TYPES.CUSTOM,
  'object': FIELD_TYPES.CUSTOM,
  'email': FIELD_TYPES.TEXT,
  'url': FIELD_TYPES.TEXT,
};

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
  validation?: (value: unknown) => ValidationResult;
}