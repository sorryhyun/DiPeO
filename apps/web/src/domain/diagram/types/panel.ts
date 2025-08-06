// Import node form data types from type factories
import type {
  StartFormData,
  PersonJobFormData,
  ConditionFormData,
  EndpointFormData,
  CodeJobFormData,
  ApiJobFormData,
  UserResponseFormData,
  NotionFormData,
  PersonBatchJobFormData,
  HookFormData,
  DBFormData as BaseDBFormData,
  DBNodeData,
  HookNodeData
} from '@/infrastructure/types/type-factories';

// Import shared panel types
import type {
  FieldType,
  PanelFormData,
  ConditionalConfig,
  OptionsConfig
} from '@/infrastructure/types/panel';

// Re-export types
export type {
  FieldType as PanelFieldType,
  PanelFormData,
  ConditionalConfig,
  OptionsConfig,
  HookNodeData,
  // Re-export all form data types
  StartFormData,
  PersonJobFormData,
  ConditionFormData,
  EndpointFormData,
  CodeJobFormData,
  ApiJobFormData,
  UserResponseFormData,
  NotionFormData,
  PersonBatchJobFormData,
  HookFormData
};

/**
 * DB form data with UI-specific field mapping
 */
export type DBFormData = BaseDBFormData & {
  source_details?: string; // Maps to different fields based on sub_type
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
  llm_config?: {
    service?: 'openai' | 'claude' | 'gemini' | 'grok';
    model?: string;
    api_key_id?: string;
    system_prompt?: string;
  };
  temperature?: number;
  type?: 'person';
  masked_api_key?: string | null;
}

// Re-export typed versions from shared types
export type {
  TypedPanelFieldConfig,
  PanelLayoutConfig
} from '@/infrastructure/types/panel';