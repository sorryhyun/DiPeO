// Configuration-driven property panel system
// This replaces hardcoded JSX components with declarative configurations

export type FieldType = 
  | 'text' 
  | 'select' 
  | 'textarea' 
  | 'checkbox' 
  | 'iterationCount' 
  | 'personSelect'
  | 'variableTextArea'
  | 'labelPersonRow'
  | 'row'
  | 'custom';

export interface BaseFieldConfig {
  type: FieldType;
  name?: string;
  label?: string;
  className?: string;
  conditional?: {
    field: string;
    values: any[];
    operator?: 'equals' | 'notEquals' | 'includes';
  };
}

export interface TextFieldConfig extends BaseFieldConfig {
  type: 'text';
  name: string;
  placeholder?: string;
}

export interface SelectFieldConfig extends BaseFieldConfig {
  type: 'select';
  name: string;
  options: Array<{ value: string; label: string }> | (() => Array<{ value: string; label: string }>);
  placeholder?: string;
}

export interface TextAreaFieldConfig extends BaseFieldConfig {
  type: 'textarea';
  name: string;
  rows?: number;
  placeholder?: string;
}

export interface CheckboxFieldConfig extends BaseFieldConfig {
  type: 'checkbox';
  name: string;
}

export interface IterationCountFieldConfig extends BaseFieldConfig {
  type: 'iterationCount';
  name: string;
  min?: number;
  max?: number;
}

export interface PersonSelectFieldConfig extends BaseFieldConfig {
  type: 'personSelect';
  name: string;
  placeholder?: string;
}

export interface VariableTextAreaFieldConfig extends BaseFieldConfig {
  type: 'variableTextArea';
  name: string;
  rows?: number;
  placeholder?: string;
}

export interface LabelPersonRowFieldConfig extends BaseFieldConfig {
  type: 'labelPersonRow';
  labelPlaceholder?: string;
  personPlaceholder?: string;
}

export interface RowFieldConfig extends BaseFieldConfig {
  type: 'row';
  fields: FieldConfig[];
}

export interface CustomFieldConfig extends BaseFieldConfig {
  type: 'custom';
  component: React.ComponentType<any>;
  props?: Record<string, any>;
}

export type FieldConfig = 
  | TextFieldConfig 
  | SelectFieldConfig 
  | TextAreaFieldConfig
  | CheckboxFieldConfig
  | IterationCountFieldConfig
  | PersonSelectFieldConfig
  | VariableTextAreaFieldConfig
  | LabelPersonRowFieldConfig
  | RowFieldConfig
  | CustomFieldConfig;

export interface ValidationRule<T> {
  field: keyof T;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any, formData: T) => string | null;
}

export type ValidationRules<T> = ValidationRule<T>[];

export interface PanelConfig<T extends Record<string, any>> {
  layout: 'single' | 'twoColumn';
  fields?: FieldConfig[];        // For single column
  leftColumn?: FieldConfig[];    // For two column
  rightColumn?: FieldConfig[];   // For two column
  validation?: ValidationRules<T>;
}

// Helper type to ensure config matches data type
export type TypedPanelConfig<T extends Record<string, any>> = PanelConfig<T> & {
  // This ensures the field names in the config match the data type
  _phantom?: T;
};

// Re-export React import for component references
import React from 'react';