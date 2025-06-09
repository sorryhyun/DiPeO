/**
 * Validation-related types for the DiPeO application
 * These types define validation structures, results, and configurations
 * used throughout the application for runtime validation.
 */

/**
 * Result of a validation operation
 */
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
}

/**
 * Configuration for node validation
 */
export interface NodeValidationConfig {
  requiredFields: string[];
  optionalFields: string[];
  customValidators?: Record<string, (value: any) => ValidationResult>;
}

/**
 * Entities that can be validated
 */
export type ValidatableEntity = 'node' | 'arrow' | 'person' | 'diagram';

/**
 * Validation error with context
 */
export interface ValidationError {
  field: string;
  message: string;
  code?: string;
  path?: string[];
}

/**
 * Extended validation result with detailed errors
 */
export interface DetailedValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings?: ValidationError[];
  data?: any; // Validated and transformed data
}

/**
 * Validator function type
 */
export type Validator<T = any> = (value: T) => ValidationResult;

/**
 * Async validator function type
 */
export type AsyncValidator<T = any> = (value: T) => Promise<ValidationResult>;

/**
 * Field validation rule
 */
export interface FieldValidationRule {
  validator: Validator | AsyncValidator;
  message?: string;
  priority?: number;
}

/**
 * Form validation configuration
 */
export interface FormValidationConfig {
  fields: Record<string, FieldValidationRule[]>;
  crossFieldValidators?: Array<{
    fields: string[];
    validator: (values: Record<string, any>) => ValidationResult;
  }>;
}


/**
 * Validation context for providing additional information during validation
 */
export interface ValidationContext {
  entity: ValidatableEntity;
  entityId?: string;
  parentContext?: ValidationContext;
  metadata?: Record<string, any>;
}