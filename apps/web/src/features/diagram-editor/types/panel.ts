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

// Import shared panel types
import type {
  FieldType,
  PanelFormData,
  ConditionalConfig,
  OptionsConfig,
  TypedPanelFieldConfig,
  BasePanelFieldConfig,
  PanelLayoutConfig
} from '@/core/types/panel';

export type {
  FieldType as PanelFieldType,
  PanelFormData,
  ConditionalConfig,
  OptionsConfig
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

// Re-export typed versions from shared types
export type {
  TypedPanelFieldConfig,
  PanelLayoutConfig
} from '@/core/types/panel';