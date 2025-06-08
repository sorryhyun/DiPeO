import { z } from 'zod';

/**
 * Custom validation error class
 */
export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly zodError?: z.ZodError,
    public readonly field?: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Format Zod error for user display
 */
export function formatZodError(error: z.ZodError): string {
  return error.errors
    .map(e => {
      const path = e.path.join('.');
      return path ? `${path}: ${e.message}` : e.message;
    })
    .join(', ');
}

/**
 * Extract field errors from Zod error
 */
export function extractFieldErrors(error: z.ZodError): Record<string, string> {
  const fieldErrors: Record<string, string> = {};
  
  for (const issue of error.errors) {
    const path = issue.path.join('.');
    if (path) {
      fieldErrors[path] = issue.message;
    }
  }
  
  return fieldErrors;
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): error is ValidationError {
  return error instanceof ValidationError;
}

/**
 * Check if error is a Zod error
 */
export function isZodError(error: unknown): error is z.ZodError {
  return error instanceof z.ZodError;
}

/**
 * Create user-friendly error messages
 */
export function createUserMessage(error: z.ZodError): string {
  const firstError = error.errors[0];
  
  if (!firstError) {
    return 'Validation failed';
  }
  
  const path = firstError.path.join('.');
  
  switch (firstError.code) {
    case 'invalid_type':
      return `${path || 'Value'} must be a ${firstError.expected}`;
      
    case 'invalid_string':
      if (firstError.validation === 'regex') {
        return `${path || 'Value'} has invalid format`;
      }
      return `${path || 'Value'} is invalid`;
      
    case 'too_small':
      return `${path || 'Value'} must be at least ${firstError.minimum}`;
      
    case 'too_big':
      return `${path || 'Value'} must be at most ${firstError.maximum}`;
      
    case 'invalid_enum_value':
      return `${path || 'Value'} must be one of: ${firstError.options?.join(', ')}`;
      
    default:
      return firstError.message;
  }
}