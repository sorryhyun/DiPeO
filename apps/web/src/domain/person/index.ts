/**
 * Person Management Feature - Public API
 * 
 * This feature manages the Person nodes (LLM agents) in DiPeO diagrams,
 * including their configuration, model selection, and runtime behavior.
 */

// ============================================
// Components
// ============================================

/**
 * Note: Person management UI is integrated into the diagram editor
 * and properties editor features. This feature primarily provides
 * hooks and utilities for managing Person nodes programmatically.
 */

// ============================================
// Hooks
// ============================================

/**
 * usePersonOperations - Main hook for Person node operations
 * Provides methods for creating, updating, and deleting Person nodes
 * Handles model configuration and validation
 */
export { usePersonOperations } from './hooks/usePersonOperations';

/**
 * usePersonsData - Hook for accessing all Person nodes in the diagram
 * Returns an array of Person nodes with their current configurations
 */
export { usePersonsData } from './hooks/usePersonsData';

// ============================================
// Factory Functions
// ============================================

/**
 * Store operation factory configuration
 * Use this for creating custom operations with the factory pattern
 */
export type { 
  OperationHookConfig,
  OperationHookReturn 
} from './hooks/factories/storeOpFactory';

// ============================================
// Types and Interfaces
// ============================================

/**
 * Person management store types
 */
export type { PersonSlice } from '@/infrastructure/store/slices/person';

/**
 * Re-export domain types for Person management
 */
export type {
  DomainPerson,
  PersonID,
  LLMService,
  PersonLLMConfig
} from '@/core/types/domain';

// ============================================
// Constants
// ============================================

/**
 * Supported LLM providers and their models
 */
export const SUPPORTED_PROVIDERS = {
  OPENAI: 'openai',
  ANTHROPIC: 'anthropic',
  GOOGLE: 'google'
} as const;

/**
 * Default model configurations by provider
 */
export const DEFAULT_MODELS = {
  openai: 'gpt-4.1-nano',
  anthropic: 'claude-3-sonnet',
  google: 'gemini-pro'
} as const;