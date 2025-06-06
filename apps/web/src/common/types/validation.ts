// Validation and flow control types
import { Arrow } from './core';

export interface ArrowValidation {
  isValid: boolean;
  arrow: Arrow;
  reason?: string;
}

export interface DependencyInfo {
  node_id: string;
  dependenciesMet: boolean;
  validArrows: Arrow[];
  missingDependencies: string[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}