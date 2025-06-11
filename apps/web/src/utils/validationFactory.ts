/**
 * Validation Factory
 * 
 * Provides consistent validation patterns and error handling
 * for form fields and entity operations.
 */

// Validation result type
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
}

// Validation rule type
export type ValidationRule<T> = (value: T) => string | null;

// Validation configuration
export interface ValidationConfig<T> {
  rules: ValidationRule<T>[];
  required?: boolean;
  requiredMessage?: string;
}

/**
 * Creates a validation function from configuration
 */
export function createValidator<T>(
  config: ValidationConfig<T>
): (value: T | undefined | null) => ValidationResult {
  return (value: T | undefined | null): ValidationResult => {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    // Check required
    if (config.required && (value === undefined || value === null || value === '')) {
      errors.push(config.requiredMessage || 'This field is required');
      return { isValid: false, errors, warnings };
    }
    
    // Skip validation if not required and empty
    if (!config.required && (value === undefined || value === null || value === '')) {
      return { isValid: true, errors: [], warnings };
    }
    
    // Run validation rules
    for (const rule of config.rules) {
      const error = rule(value as T);
      if (error) {
        errors.push(error);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  };
}

/**
 * Common validation rules
 */
export const ValidationRules = {
  // String validations
  minLength: (min: number): ValidationRule<string> =>
    (value) => value.length < min ? `Must be at least ${min} characters` : null,
    
  maxLength: (max: number): ValidationRule<string> =>
    (value) => value.length > max ? `Must be at most ${max} characters` : null,
    
  pattern: (pattern: RegExp, message: string): ValidationRule<string> =>
    (value) => !pattern.test(value) ? message : null,
    
  email: (): ValidationRule<string> =>
    (value) => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? 'Invalid email address' : null,
    
  url: (): ValidationRule<string> =>
    (value) => {
      try {
        new URL(value);
        return null;
      } catch {
        return 'Invalid URL';
      }
    },
    
  // Number validations
  min: (min: number): ValidationRule<number> =>
    (value) => value < min ? `Must be at least ${min}` : null,
    
  max: (max: number): ValidationRule<number> =>
    (value) => value > max ? `Must be at most ${max}` : null,
    
  integer: (): ValidationRule<number> =>
    (value) => !Number.isInteger(value) ? 'Must be an integer' : null,
    
  positive: (): ValidationRule<number> =>
    (value) => value <= 0 ? 'Must be positive' : null,
    
  // Array validations
  minItems: <T>(min: number): ValidationRule<T[]> =>
    (value) => value.length < min ? `Must have at least ${min} items` : null,
    
  maxItems: <T>(max: number): ValidationRule<T[]> =>
    (value) => value.length > max ? `Must have at most ${max} items` : null,
    
  uniqueItems: <T>(): ValidationRule<T[]> =>
    (value) => {
      const seen = new Set();
      for (const item of value) {
        const key = typeof item === 'object' ? JSON.stringify(item) : item;
        if (seen.has(key)) {
          return 'Items must be unique';
        }
        seen.add(key);
      }
      return null;
    },
    
  // Custom validations
  oneOf: <T>(options: T[], message?: string): ValidationRule<T> =>
    (value) => !options.includes(value) 
      ? message || `Must be one of: ${options.join(', ')}` 
      : null,
      
  notEmpty: (): ValidationRule<string> =>
    (value) => !value.trim() ? 'Cannot be empty' : null,
    
  alphanumeric: (): ValidationRule<string> =>
    (value) => !/^[a-zA-Z0-9]+$/.test(value) ? 'Must be alphanumeric' : null,
    
  identifier: (): ValidationRule<string> =>
    (value) => !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(value) 
      ? 'Must be a valid identifier (letters, numbers, underscore)' 
      : null,
      
  jsonString: (): ValidationRule<string> =>
    (value) => {
      try {
        JSON.parse(value);
        return null;
      } catch {
        return 'Must be valid JSON';
      }
    }
};

/**
 * Creates a composite validator from multiple validators
 */
export function combineValidators<T>(
  ...validators: Array<(value: T) => ValidationResult>
): (value: T) => ValidationResult {
  return (value: T): ValidationResult => {
    const allErrors: string[] = [];
    const allWarnings: string[] = [];
    let isValid = true;
    
    for (const validator of validators) {
      const result = validator(value);
      if (!result.isValid) {
        isValid = false;
      }
      allErrors.push(...result.errors);
      if (result.warnings) {
        allWarnings.push(...result.warnings);
      }
    }
    
    return {
      isValid,
      errors: allErrors,
      warnings: allWarnings.length > 0 ? allWarnings : undefined
    };
  };
}

/**
 * Creates a field validator for objects
 */
export function createFieldValidator<T extends Record<string, any>>(
  fieldConfigs: { [K in keyof T]?: ValidationConfig<T[K]> }
): (obj: Partial<T>) => Record<keyof T, ValidationResult> {
  const validators: Record<string, (value: any) => ValidationResult> = {};
  
  // Create validators for each field
  for (const [field, config] of Object.entries(fieldConfigs)) {
    if (config) {
      validators[field] = createValidator(config as any);
    }
  }
  
  return (obj: Partial<T>) => {
    const results: Record<string, ValidationResult> = {};
    
    for (const [field, validator] of Object.entries(validators)) {
      results[field] = validator(obj[field as keyof T]);
    }
    
    return results as Record<keyof T, ValidationResult>;
  };
}

/**
 * Validates all fields and returns combined result
 */
export function validateAll<T extends Record<string, any>>(
  obj: Partial<T>,
  fieldValidator: (obj: Partial<T>) => Record<keyof T, ValidationResult>
): ValidationResult {
  const fieldResults = fieldValidator(obj);
  const allErrors: string[] = [];
  const allWarnings: string[] = [];
  let isValid = true;
  
  for (const [field, result] of Object.entries(fieldResults)) {
    if (!result.isValid) {
      isValid = false;
      // Prefix errors with field name
      allErrors.push(...result.errors.map(err => `${field}: ${err}`));
    }
    if (result.warnings) {
      allWarnings.push(...result.warnings.map(warn => `${field}: ${warn}`));
    }
  }
  
  return {
    isValid,
    errors: allErrors,
    warnings: allWarnings.length > 0 ? allWarnings : undefined
  };
}

/**
 * Creates async validator for server-side validation
 */
export function createAsyncValidator<T>(
  validator: (value: T) => Promise<string | null>
): (value: T) => Promise<ValidationResult> {
  return async (value: T): Promise<ValidationResult> => {
    try {
      const error = await validator(value);
      return {
        isValid: !error,
        errors: error ? [error] : []
      };
    } catch (err) {
      return {
        isValid: false,
        errors: ['Validation failed: ' + (err instanceof Error ? err.message : 'Unknown error')]
      };
    }
  };
}