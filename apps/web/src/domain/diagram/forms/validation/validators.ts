import type { FieldValidator, ValidationResult } from '../types';

export const createValidator = (
  validate: (value: any, formData?: Record<string, any>) => boolean | string,
  defaultMessage = 'Validation failed'
): FieldValidator => {
  return (value, formData) => {
    const result = validate(value, formData);

    if (result === true) {
      return { valid: true, errors: [] };
    }

    const message = typeof result === 'string' ? result : defaultMessage;

    return {
      valid: false,
      errors: [{ field: '', message }],
    };
  };
};

export const required = (message = 'This field is required'): FieldValidator =>
  createValidator(value => {
    if (value === null || value === undefined || value === '') return message;
    if (Array.isArray(value) && value.length === 0) return message;
    if (typeof value === 'object' && Object.keys(value).length === 0) return message;
    return true;
  });

export const minLength = (min: number, message?: string): FieldValidator =>
  createValidator(
    value => {
      if (!value) return true;
      const length = typeof value === 'string' ? value.length : value.length || 0;
      return length >= min || message || `Must be at least ${min} characters`;
    }
  );

export const maxLength = (max: number, message?: string): FieldValidator =>
  createValidator(
    value => {
      if (!value) return true;
      const length = typeof value === 'string' ? value.length : value.length || 0;
      return length <= max || message || `Must be at most ${max} characters`;
    }
  );

export const pattern = (regex: RegExp, message = 'Invalid format'): FieldValidator =>
  createValidator(value => {
    if (!value) return true;
    return regex.test(String(value)) || message;
  });

export const email = (message = 'Invalid email address'): FieldValidator =>
  pattern(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, message);

export const url = (message = 'Invalid URL'): FieldValidator =>
  createValidator(value => {
    if (!value) return true;
    try {
      new URL(value);
      return true;
    } catch {
      return message;
    }
  });

export const min = (minValue: number, message?: string): FieldValidator =>
  createValidator(
    value => {
      if (value === null || value === undefined || value === '') return true;
      const num = Number(value);
      return (!isNaN(num) && num >= minValue) || message || `Must be at least ${minValue}`;
    }
  );

export const max = (maxValue: number, message?: string): FieldValidator =>
  createValidator(
    value => {
      if (value === null || value === undefined || value === '') return true;
      const num = Number(value);
      return (!isNaN(num) && num <= maxValue) || message || `Must be at most ${maxValue}`;
    }
  );

export const integer = (message = 'Must be a whole number'): FieldValidator =>
  createValidator(value => {
    if (value === null || value === undefined || value === '') return true;
    const num = Number(value);
    return (!isNaN(num) && Number.isInteger(num)) || message;
  });

export const oneOf = <T>(values: T[], message?: string): FieldValidator =>
  createValidator(
    value => {
      if (!value) return true;
      return values.includes(value) || message || `Must be one of: ${values.join(', ')}`;
    }
  );

export const compose = (...validators: FieldValidator[]): FieldValidator => {
  return async (value, formData) => {
    const errors: ValidationResult['errors'] = [];

    for (const validator of validators) {
      const result = await validator(value, formData);
      if (!result.valid) {
        errors.push(...result.errors);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  };
};

export const conditional = (
  condition: (value: any, formData?: Record<string, any>) => boolean,
  validator: FieldValidator
): FieldValidator => {
  return (value, formData) => {
    if (!condition(value, formData)) {
      return { valid: true, errors: [] };
    }
    return validator(value, formData);
  };
};

export const dependsOn = (
  dependency: string,
  validator: (depValue: any) => FieldValidator
): FieldValidator => {
  return (value, formData) => {
    const depValue = formData?.[dependency];
    return validator(depValue)(value, formData);
  };
};
