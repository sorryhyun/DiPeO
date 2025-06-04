// Validation and flow control types
import { Arrow } from './arrow';

export interface ArrowValidation {
  isValid: boolean;
  arrow: Arrow;
  reason?: string;
}

export interface DependencyInfo {
  nodeId: string;
  dependenciesMet: boolean;
  validArrows: Arrow[];
  missingDependencies: string[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}