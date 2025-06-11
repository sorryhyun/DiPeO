/**
 * Type Guards
 * 
 * This file re-exports type guards from the refactored implementation
 * using the type guard factory pattern for consistency and reduced duplication.
 */

// Re-export all type guards from the refactored implementation
export {
  // Entity type guards
  isApiKey,
  isDomainArrow,
  isDomainHandle,
  
  // Handle type guards
  isInputHandle,
  isOutputHandle,
  
  // Enum type guards
  isNodeKind,
  isApiService,
  isLLMService,
  isHandleDirection,
  
  // Branded type guards
  isNodeId,
  isHandleId,
  isArrowId,
  isPersonId,
  isApiKeyId,
  
  // Collection type guards
  isApiKeyArray,
  isDomainNodeArray,
  isDomainArrowArray,
  isDomainHandleArray,
  isDomainPersonArray,
  
  // Utility type guards
  isPosition,
  isSize,
  isRect,
  
  // Helper functions
  parseApiArrayResponse,
  
  // Universal type guard
  isDomainEntity,
  
  // Types
  type AnyDomainEntity
} from './typeGuardsRefactored';

// Also export from domain for backward compatibility
export type { DomainApiKey, DomainArrow, DomainHandle, InputHandle, OutputHandle } from './domain';
export type { NodeKind } from './primitives';