// UI types - State management, component interfaces, and form configurations
import React from 'react';

// UI State Types
export interface UIState {
  selectedId: string | null;
  selectedType: 'node' | 'arrow' | 'person' | null;
  activeView: 'diagram' | 'memory' | 'execution' | 'conversation';
  isMonitorMode: boolean;
  isPropertyPanelOpen: boolean;
  contextMenu: {
    isOpen: boolean;
    position: { x: number; y: number };
    nodeId?: string;
  } | null;
}

export interface SelectionState {
  id: string;
  type: 'node' | 'arrow' | 'person';
}

export interface ModalState {
  apiKeys: boolean;
  interactivePrompt: boolean;
  fileImport: boolean;
}

export interface NotificationState {
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
}

export interface CanvasState {
  zoom: number;
  center: { x: number; y: number };
  isDragging: boolean;
  isConnecting: boolean;
}

export interface PropertyPanelState {
  isOpen: boolean;
  isDirty: boolean;
  errors: Record<string, string>;
}

// Component Props Types
export interface FormFieldProps {
  label: string;
  id?: string;
  children: React.ReactNode;
  className?: string;
}

export interface PanelProps {
  icon?: React.ReactNode;
  title: string;
  children: React.ReactNode;
}

// Field Configuration Types
export interface FieldConfig {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'string' | 'boolean' | 'person' | 'file';
  placeholder?: string;
  isRequired?: boolean;
  required?: boolean;
  options?: { value: string; label: string }[];
  rows?: number;
  hint?: string;
  helperText?: string;
  multiline?: boolean;
  min?: number;
  max?: number;
  acceptedFileTypes?: string;
  customProps?: Record<string, any>;
  disabled?: boolean;
}

export type PropertyFieldConfig = FieldConfig;

// Panel Configuration Types
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
    values: unknown[];
    operator?: 'equals' | 'notEquals' | 'includes';
  };
}

export interface TextFieldConfig extends BaseFieldConfig {
  type: 'text';
  name: string;
  placeholder?: string;
  disabled?: boolean;
}

export interface SelectFieldConfig extends BaseFieldConfig {
  type: 'select';
  name: string;
  options: Array<{ value: string; label: string }> | (() => Array<{ value: string; label: string }>) | (() => Promise<Array<{ value: string; label: string }>>) | ((formData: unknown) => Promise<Array<{ value: string; label: string }>>);
  placeholder?: string;
  disabled?: boolean;
  dependsOn?: string[];
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
  fields: PanelFieldConfig[];
}

export interface CustomFieldConfig extends BaseFieldConfig {
  type: 'custom';
  component: React.ComponentType<unknown>;
  props?: Record<string, unknown>;
}

export type PanelFieldConfig = 
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
  custom?: (value: unknown, formData: T) => string | null;
}

export type ValidationRules<T> = ValidationRule<T>[];

export interface PanelConfig<T> {
  layout: 'single' | 'twoColumn';
  fields?: PanelFieldConfig[];
  leftColumn?: PanelFieldConfig[];
  rightColumn?: PanelFieldConfig[];
  validation?: ValidationRules<T>;
}

export type TypedPanelConfig<T extends Record<string, unknown>> = PanelConfig<T> & {
  _phantom?: T;
};