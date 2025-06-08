/**
 * Validation types for nodes and other entities
 */

/**
 * General validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Node validation configuration
 */
export interface NodeValidationConfig {
  required?: string[];
  optional?: string[];
  validators?: Record<string, (value: unknown) => ValidationResult>;
}

/**
 * Entity validation types
 */
export type ValidatableEntity = 'node' | 'arrow' | 'person' | 'diagram';