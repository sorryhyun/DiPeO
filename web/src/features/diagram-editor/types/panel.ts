import type {
  StartNodeData,
  ConditionNodeData,
  PersonJobNodeData,
  EndpointNodeData,
  DBNodeData,
  JobNodeData,
  UserResponseNodeData,
  NotionNodeData,
  PersonBatchJobNodeData
} from '@/core/types';

/**
 * Extended field types for property panels
 * These map to specific UI components in the property panel
 */
export type PanelFieldType = 
  | 'text' 
  | 'select' 
  | 'textarea' 
  | 'variableTextArea' 
  | 'checkbox'
  | 'maxIteration' 
  | 'personSelect' 
  | 'labelPersonRow' 
  | 'row' 
  | 'custom';

/**
 * Conditional rendering configuration
 */
export interface ConditionalConfig {
  field: string;
  values: unknown[];
  operator?: 'equals' | 'notEquals' | 'includes';
}

/**
 * Options configuration for select fields
 */
export type OptionsConfig<T = unknown> = 
  | Array<{ value: string; label: string }>
  | (() => Promise<Array<{ value: string; label: string }>>)
  | ((formData: T) => Promise<Array<{ value: string; label: string }>>);

/**
 * Panel-specific field configuration
 * This is a UI-specific configuration that maps to domain field properties
 */
export interface PanelFieldConfig {
  type: PanelFieldType;
  name?: string;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  rows?: number;
  min?: number;
  max?: number;
  className?: string;
  options?: OptionsConfig;
  dependsOn?: string[];
  conditional?: ConditionalConfig;
  // For row type - allows nested field groups
  fields?: PanelFieldConfig[];
  // For labelPersonRow type - special placeholders
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

/**
 * Generic form data wrapper that allows UI-specific extensions
 * while maintaining type safety with domain types
 */
export type PanelFormData<T extends Record<string, unknown>> = Partial<T> & {
  // Allow additional UI-specific fields for runtime flexibility
  [key: string]: unknown;
};

// Node form data types - directly map to domain node data
export type StartFormData = PanelFormData<StartNodeData>;
export type PersonJobFormData = PanelFormData<PersonJobNodeData>;
export type ConditionFormData = PanelFormData<ConditionNodeData>;
export type EndpointFormData = PanelFormData<EndpointNodeData>;
export type JobFormData = PanelFormData<JobNodeData>;
export type UserResponseFormData = PanelFormData<UserResponseNodeData>;
export type NotionFormData = PanelFormData<NotionNodeData>;
export type PersonBatchJobFormData = PanelFormData<PersonBatchJobNodeData>;

/**
 * DB form data with UI-specific field mapping
 */
export type DBFormData = PanelFormData<DBNodeData> & {
  sourceDetails?: string; // Maps to different fields based on subType
};
/**
 * Arrow form data - extends domain arrow with UI fields
 */
export interface ArrowFormData extends Record<string, unknown> {
  label?: string;
  outputMappings?: Array<{ from: string; to: string }>;
}

/**
 * Person form data - maps to DomainPerson properties
 */
export interface PersonFormData extends Record<string, unknown> {
  label?: string;
  service?: 'openai' | 'claude' | 'gemini' | 'grok';
  model?: string;
  temperature?: number;
  maxTokens?: number;
  apiKeyId?: string;
}

/**
 * Type-safe options loader - reuses OptionsConfig pattern
 */
export type OptionsLoader<T = unknown> = OptionsConfig<T>;

/**
 * Type-safe conditional configuration
 */
export interface TypedConditionalConfig<T> {
  field: keyof T & string;
  values: unknown[];
  operator?: 'equals' | 'notEquals' | 'includes';
}

/**
 * Enhanced panel field config with generic type safety
 */
export interface TypedPanelFieldConfig<T = unknown> extends Omit<PanelFieldConfig, 'name' | 'dependsOn' | 'conditional' | 'options' | 'fields' | 'disabled'> {
  name?: keyof T & string;
  disabled?: boolean | ((formData: T) => boolean);
  options?: OptionsLoader<T>;
  dependsOn?: Array<keyof T & string>;
  conditional?: TypedConditionalConfig<T>;
  // For row type - typed nested fields
  fields?: Array<TypedPanelFieldConfig<T>>;
  // Validation
  validate?: (value: unknown, formData: T) => { isValid: boolean; error?: string };
}

/**
 * Enhanced panel config with type safety
 */
export interface TypedPanelConfig<T extends Record<string, unknown> = Record<string, unknown>> {
  layout: 'single' | 'twoColumn';
  fields?: Array<TypedPanelFieldConfig<T>>;
  leftColumn?: Array<TypedPanelFieldConfig<T>>;
  rightColumn?: Array<TypedPanelFieldConfig<T>>;
  // Global validation
  validate?: (formData: T) => { isValid: boolean; errors?: Record<string, string> };
}