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