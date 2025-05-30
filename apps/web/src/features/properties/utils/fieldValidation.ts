/**
 * Field validation utilities for property panels
 */

export interface FieldValidationResult {
  isValid: boolean;
  error?: string;
  warning?: string;
}

export const validateTextField = (value: string, required = false): FieldValidationResult => {
  if (required && (!value || value.trim().length === 0)) {
    return { isValid: false, error: 'This field is required' };
  }

  if (value && value.length > 1000) {
    return { isValid: false, error: 'Text is too long (max 1000 characters)' };
  }

  return { isValid: true };
};

export const validateNumberField = (value: string, min?: number, max?: number): FieldValidationResult => {
  if (!value) {
    return { isValid: true };
  }

  const num = Number(value);
  if (isNaN(num)) {
    return { isValid: false, error: 'Must be a valid number' };
  }

  if (min !== undefined && num < min) {
    return { isValid: false, error: `Must be at least ${min}` };
  }

  if (max !== undefined && num > max) {
    return { isValid: false, error: `Must be at most ${max}` };
  }

  return { isValid: true };
};

export const validateEmailField = (value: string): FieldValidationResult => {
  if (!value) {
    return { isValid: true };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    return { isValid: false, error: 'Must be a valid email address' };
  }

  return { isValid: true };
};

export const validateUrlField = (value: string): FieldValidationResult => {
  if (!value) {
    return { isValid: true };
  }

  try {
    new URL(value);
    return { isValid: true };
  } catch {
    return { isValid: false, error: 'Must be a valid URL' };
  }
};

export const validateJsonField = (value: string): FieldValidationResult => {
  if (!value) {
    return { isValid: true };
  }

  try {
    JSON.parse(value);
    return { isValid: true };
  } catch {
    return { isValid: false, error: 'Must be valid JSON' };
  }
};