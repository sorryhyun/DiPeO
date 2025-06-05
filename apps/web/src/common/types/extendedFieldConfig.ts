import { FieldConfig } from './nodeConfig';

/**
 * Extended field configuration that supports all field types used in the application
 */
export interface ExtendedFieldConfig extends Omit<FieldConfig, 'type'> {
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
export type PropertyFieldConfig = ExtendedFieldConfig;