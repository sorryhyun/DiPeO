import { Node } from '@xyflow/react';

/**
 * Node validation utilities
 */

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export const validateNode = (node: Node): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Basic validation
  if (!node.id) {
    errors.push('Node must have an ID');
  }

  if (!node.type) {
    errors.push('Node must have a type');
  }

  if (!node.data) {
    errors.push('Node must have data');
  }

  // Position validation
  if (!node.position) {
    warnings.push('Node position not set');
  }

  // Type-specific validation could be added here
  switch (node.type) {
    case 'person':
      if (!node.data?.name) {
        warnings.push('Person node should have a name');
      }
      break;
    case 'job':
      if (!node.data?.prompt) {
        warnings.push('Job node should have a prompt');
      }
      break;
    default:
      break;
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
};

export const validateNodeData = (nodeType: string, data: unknown): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data) {
    errors.push('Node data is required');
    return { isValid: false, errors, warnings };
  }

  // Add type-specific data validation here

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
};