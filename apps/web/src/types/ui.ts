// types/ui.ts - UI-related types

import type { Vec2, Dict } from './primitives';
import type { NodeID, ArrowID, PersonID } from './branded';
import type { Node, Arrow, Person, ApiKey } from './diagram';
import type React from 'react';

export const Views = ['diagram','memory','execution','conversation'] as const;
export type View = typeof Views[number];

export interface UIState {
  selected?: { id: NodeID | ArrowID | PersonID; kind: 'node' | 'arrow' | 'person' };
  active: View;
  monitorMode: boolean;
  propertyPanelOpen: boolean;
  contextMenu?: { pos: Vec2; nodeId?: NodeID };
}

/* Canvas */
export interface CanvasState {
  zoom: number;
  center: Vec2;
  dragging: boolean;
  connecting: boolean;
}

export interface PropertyPanelState {
  open: boolean;
  dirty: boolean;
  errors: Dict<string>;
}

/* Field Configuration */
export type FieldType = 
  | 'text' 
  | 'select' 
  | 'textarea' 
  | 'checkbox' 
  | 'number'
  | 'boolean'
  | 'string'
  | 'file'
  | 'person'
  | 'maxIteration'
  | 'personSelect'
  | 'variableTextArea'
  | 'labelPersonRow'
  | 'row'
  | 'custom';

export interface FieldConfig<T = unknown> {
  name: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  required?: boolean;
  options?: Array<{ value: string; label: string }> | (() => Array<{ value: string; label: string }>);
  rows?: number;
  hint?: string;
  min?: number;
  max?: number;
  acceptedFileTypes?: string;
  disabled?: boolean;
  conditional?: {
    field: string;
    values: T[];
    operator?: 'equals' | 'notEquals' | 'includes';
  };
  className?: string;
  dependsOn?: string[];
}

/* Panel Configuration */
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

export interface MaxIterationFieldConfig extends BaseFieldConfig {
  type: 'maxIteration';
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
  | MaxIterationFieldConfig
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

export interface PanelConfig<T = Dict> {
  layout: 'single' | 'twoColumn';
  fields?: PanelFieldConfig[];
  leftColumn?: PanelFieldConfig[];
  rightColumn?: PanelFieldConfig[];
  validation?: ValidationRules<T>;
}

export type TypedPanelConfig<T extends Dict> = PanelConfig<T> & {
  _phantom?: T;
};

/* UI Component State */
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

export interface ConversationFilters {
  searchTerm?: string;
  executionId?: string;
  showForgotten?: boolean;
  startTime?: string;
  endTime?: string;
}

/* Store State Types */
export interface DiagramState {
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
}

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