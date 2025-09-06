/**
 * Node specification types for DiPeO codegen system
 * These types define the structure of node specifications that drive code generation
 */

import { NodeType } from '../core/enums/node-types.js';
import { DataType } from '../core/enums/data-types.js';
import { SupportedLanguage } from '../core/enums/node-specific.js';
import { NodeCategory, FieldType, UIInputType } from './categories.js';

/**
 * Validation rules for a field
 */
export interface ValidationRules {
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  message?: string;
  itemType?: FieldType;
  allowedValues?: string[];
}

/**
 * UI configuration for a field
 */
export interface UIConfiguration {
  inputType: UIInputType;
  placeholder?: string;
  column?: 1 | 2;  // Column placement in form
  rows?: number;   // For textarea
  language?: SupportedLanguage;  // For code editor
  collapsible?: boolean;
  readOnly?: boolean;
  options?: Array<{ value: string; label: string }>;  // For select
  min?: number;    // For number input
  max?: number;    // For number input
  showPromptFileButton?: boolean;  // Show button to load prompt from file
  adjustable?: boolean;  // Allow field to be resized
  hidden?: boolean;  // Hide field from UI (but keep in data model)
}

/**
 * Conditional display configuration
 */
export interface ConditionalConfig {
  field: string;  // Field name to check
  values: any[];  // Values that make this field visible
  operator?: 'equals' | 'notEquals' | 'includes';  // Default: 'includes'
}

/**
 * Field specification defining a single field in a node
 */
export interface FieldSpecification {
  name: string;
  type: FieldType;
  required: boolean;
  description: string;
  defaultValue?: any;
  validation?: ValidationRules;
  uiConfig: UIConfiguration;
  nestedFields?: FieldSpecification[];  // For object types
  affects?: string[];  // Other fields affected by this field's value
  conditional?: ConditionalConfig;  // Show/hide field based on another field's value
}

/**
 * Handle configuration for a node
 */
export interface HandleConfiguration {
  inputs: string[];
  outputs: string[];
}

/**
 * Input port specification for SEAC (Strict Envelopes & Arrow Contracts)
 */
export interface InputPortSpecification {
  name?: string;  // Port name (omit for single unnamed port)
  contentType: 'raw_text' | 'object' | 'conversation_state' | 'binary';
  required: boolean;
  default?: any;  // Default value if not connected
  accepts?: string[];  // Type hints for validation
  description?: string;
}

/**
 * Output specification for a node
 */
export interface OutputSpecification {
  type: DataType | 'any';
  description: string;
}

/**
 * Execution configuration for a node
 */
export interface ExecutionConfiguration {
  timeout?: number;        // Default timeout in seconds
  retryable?: boolean;     // Can be retried on failure
  maxRetries?: number;     // Maximum retry attempts
  requires?: string[];     // Required dependencies/libraries
}

/**
 * Example configuration for documentation
 */
export interface ExampleConfiguration {
  name: string;
  description: string;
  configuration: Record<string, any>;
}

/**
 * Complete node specification
 */
export interface NodeSpecification {
  nodeType: NodeType;
  displayName: string;
  category: NodeCategory;
  icon: string;
  color: string;
  description: string;
  fields: FieldSpecification[];
  handles: HandleConfiguration;
  inputPorts?: InputPortSpecification[];  // SEAC: Port contracts for inputs
  outputs?: Record<string, OutputSpecification>;
  execution?: ExecutionConfiguration;
  examples?: ExampleConfiguration[];
  primaryDisplayField?: string;  // Field name to show when node is not hovered
}

/**
 * Collection of all node specifications
 */
export interface NodeSpecificationRegistry {
  [nodeType: string]: NodeSpecification;
}

// Type guard to check if a value is a valid NodeSpecification
export function isNodeSpecification(value: any): value is NodeSpecification {
  return (
    typeof value === 'object' &&
    value !== null &&
    'nodeType' in value &&
    'displayName' in value &&
    'category' in value &&
    'fields' in value &&
    Array.isArray(value.fields) &&
    'handles' in value
  );
}

// Helper to validate field specification
export function validateFieldSpecification(field: FieldSpecification): string[] {
  const errors: string[] = [];

  if (!field.name) {
    errors.push('Field name is required');
  }

  if (!field.type) {
    errors.push('Field type is required');
  }

  if (!field.uiConfig || !field.uiConfig.inputType) {
    errors.push(`Field ${field.name} must have uiConfig with inputType`);
  }

  if (field.type === 'object' && !field.nestedFields) {
    errors.push(`Object field ${field.name} must have nestedFields`);
  }

  return errors;
}
