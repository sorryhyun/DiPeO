/**
 * Property and field utilities - form field operations only
 * API operations should be imported directly from apiClient
 */

import type { FieldValidationResult } from '@/types';

export const formatPropertyValue = (value: unknown, type: string): string => {
  if (value === null || value === undefined) {
    return '';
  }

  switch (type) {
    case 'boolean':
      return value ? 'true' : 'false';
    case 'number':
      return Number(value).toString();
    case 'array':
      return Array.isArray(value) ? value.join(', ') : '';
    case 'object':
      return typeof value === 'object' ? JSON.stringify(value, null, 2) : '';
    default:
      return String(value);
  }
};

export const parsePropertyValue = (value: string, type: string): unknown => {
  if (!value) {
    return type === 'boolean' ? false : type === 'number' ? 0 : '';
  }

  switch (type) {
    case 'boolean':
      return value.toLowerCase() === 'true';
    case 'number': {
      const num = Number(value);
      return isNaN(num) ? 0 : num;
    }
    case 'array':
      return value.split(',').map(item => item.trim()).filter(Boolean);
    case 'object':
      try {
        return JSON.parse(value);
      } catch {
        return {};
      }
    default:
      return value;
  }
};

export const getPropertyDisplayName = (key: string): string => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

export const shouldShowProperty = (key: string, value: unknown): boolean => {
  // Hide internal properties
  if (key.startsWith('_') || key.startsWith('__')) {
    return false;
  }

  // Hide undefined/null values for optional properties
  if (value === undefined || value === null) {
    return false;
  }

  return true;
};


/**
 * Field validation functions
 */
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

