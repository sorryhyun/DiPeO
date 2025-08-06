/**
 * Core type exports
 * Domain types are centralized in './domain'
 */

// Domain types and utilities (single source of truth)
export * from './domain';

// Type factory utilities
export * from './type-factories';

// UI-specific branded types and utilities  
export * from './branded';

// Type guards for UI and domain types
export * from './guards';

// Other UI-specific types
export * from './errors';
// Export utilities except DataType to avoid conflict with domain export
export { 
  generateId,
  generatePrefixedId,
  generateApiKeyId,
  generateNodeId,
  generateArrowId,
  generatePersonId,
  entityIdGenerators,
  type Dict,
  type ExtendedDataType
} from './utilities';
// Export panel types except PanelFormData which comes from type-factories
export { 
  FIELD_TYPES,
  type FieldType,
  type ValidationResult,
  type FieldValidator,
  type OptionsConfig,
  type ConditionalConfig,
  type BasePanelFieldConfig,
  type TypedPanelFieldConfig,
  type PanelLayoutConfig,
  type FieldChangeHandler,
  type PanelFormProps,
  createPanelFormData,
  FieldConfigBuilder,
  field
} from './panel';
// Export conversation types with renamed types
export {
  type InteractivePromptData as UIInteractivePromptData,
  type ConversationFilters,
  type UIConversationMessage,
  type UIPersonMemoryState
} from './conversation';

// Store-specific types
// TODO: Consider moving these to the store module
export type { SelectableID, SelectableType } from '@/infrastructure/store/slices/ui';