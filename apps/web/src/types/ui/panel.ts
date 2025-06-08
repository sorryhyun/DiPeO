export interface PanelFieldConfig {
  type: 'text' | 'select' | 'textarea' | 'variableTextArea' | 'checkbox' | 
        'maxIteration' | 'personSelect' | 'labelPersonRow' | 'row' | 'custom';
  name?: string;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  rows?: number;
  min?: number;
  max?: number;
  className?: string;
  options?: Array<{ value: string; label: string }> | (() => Promise<Array<{ value: string; label: string }>>) | ((formData: unknown) => Promise<Array<{ value: string; label: string }>>);
  dependsOn?: string[];
  conditional?: {
    field: string;
    values: unknown[];
    operator?: 'equals' | 'notEquals' | 'includes';
  };
  // For row type
  fields?: PanelFieldConfig[];
  // For labelPersonRow type
  labelPlaceholder?: string;
  personPlaceholder?: string;
}

/**
 * Panel configuration for property forms
 */
export interface PanelConfig<_T extends Record<string, unknown> = Record<string, unknown>> {
  layout: 'single' | 'twoColumn';
  fields?: PanelFieldConfig[];
  leftColumn?: PanelFieldConfig[];
  rightColumn?: PanelFieldConfig[];
}

/**
 * Panel form data types - Maps domain models to form representations
 */

import type {
  StartNodeData,
  PersonJobNodeData,
  ConditionNodeData,
  DBNodeData,
  EndpointNodeData,
  JobNodeData,
  NotionNodeData,
  UserResponseNodeData,
  PersonBatchJobNodeData
} from '../domain';

/**
 * Form data type that extends domain data with UI-specific fields
 */
export type PanelFormData<T extends Record<string, unknown>> = T & {
  // Allow additional UI-specific fields
  [key: string]: unknown;
};

/**
 * Start node form data
 */
export type StartFormData = PanelFormData<StartNodeData>;

/**
 * Person job form data with UI fields
 */
export interface PersonJobFormData extends PersonJobNodeData {
  contextCleaningRule?: 'upon_request' | 'no_forget' | 'on_every_turn';
  maxIteration?: number; // UI uses different name than domain
}

/**
 * Condition node form data with UI fields
 */
export interface ConditionFormData extends ConditionNodeData {
  conditionType?: 'expression' | 'detect_max_iterations';
  expression?: string; // Maps to 'condition' in domain
}

/**
 * DB node form data with UI fields
 */
export interface DBFormData extends DBNodeData {
  subType?: 'fixed_prompt' | 'file';
  sourceDetails?: string; // Maps to different fields based on subType
}

/**
 * Endpoint node form data
 */
export type EndpointFormData = PanelFormData<EndpointNodeData>;

/**
 * Job node form data
 */
export type JobFormData = PanelFormData<JobNodeData>;

/**
 * Notion node form data with UI fields
 */
export interface NotionFormData extends NotionNodeData {
  pageId?: string;
  content?: string;
}

/**
 * User response form data
 */
export type UserResponseFormData = PanelFormData<UserResponseNodeData>;

/**
 * Person batch job form data
 */
export interface PersonBatchJobFormData extends PersonBatchJobNodeData {
  contextCleaningRule?: 'upon_request' | 'no_forget' | 'on_every_turn';
}

/**
 * Arrow form data
 */
export interface ArrowFormData extends Record<string, unknown> {
  label?: string;
  outputMappings?: Array<{ from: string; to: string }>;
}

/**
 * Person form data
 */
export interface PersonFormData extends Record<string, unknown> {
  name: string;
  service: 'openai' | 'anthropic' | 'gemini' | 'groq' | 'xai';
  model: string;
  temperature?: number;
  maxTokens?: number;
  apiKey?: string;
}

/**
 * Type-safe options loader
 */
export type OptionsLoader<T = unknown> =
  | Array<{ value: string; label: string }>
  | (() => Promise<Array<{ value: string; label: string }>>)
  | ((formData: T) => Promise<Array<{ value: string; label: string }>>);

/**
 * Enhanced panel field config with better typing
 */
export interface TypedPanelFieldConfig<T = unknown> {
  type: 'text' | 'select' | 'textarea' | 'variableTextArea' | 'checkbox' |
        'maxIteration' | 'personSelect' | 'labelPersonRow' | 'row' | 'custom';
  name?: keyof T & string;
  label?: string;
  placeholder?: string;
  disabled?: boolean | ((formData: T) => boolean);
  required?: boolean;
  rows?: number;
  min?: number;
  max?: number;
  className?: string;
  options?: OptionsLoader<T>;
  dependsOn?: Array<keyof T & string>;
  conditional?: {
    field: keyof T & string;
    values: unknown[];
    operator?: 'equals' | 'notEquals' | 'includes';
  };
  // For row type
  fields?: Array<TypedPanelFieldConfig<T>>;
  // For labelPersonRow type
  labelPlaceholder?: string;
  personPlaceholder?: string;
  // Validation
  validate?: (value: unknown, formData: T) => { isValid: boolean; error?: string };
}

/**
 * Enhanced panel config with better typing
 */
export interface TypedPanelConfig<T extends Record<string, unknown> = Record<string, unknown>> {
  layout: 'single' | 'twoColumn';
  fields?: Array<TypedPanelFieldConfig<T>>;
  leftColumn?: Array<TypedPanelFieldConfig<T>>;
  rightColumn?: Array<TypedPanelFieldConfig<T>>;
  // Global validation
  validate?: (formData: T) => { isValid: boolean; errors?: Record<string, string> };
}