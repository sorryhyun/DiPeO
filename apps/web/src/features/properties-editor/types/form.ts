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
// Import from centralized field type registry
import { PROPERTY_TO_BASE_FIELD_TYPE } from '@/core/types/fieldTypeRegistry';
export { PROPERTY_TO_BASE_FIELD_TYPE };

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