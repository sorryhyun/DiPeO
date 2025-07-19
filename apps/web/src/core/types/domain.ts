/**
 * Centralized domain type exports from @dipeo/domain-models
 * This file serves as the single source of truth for domain types in the frontend
 * All domain types should be imported from here, not directly from @dipeo/domain-models
 */

// Core Enums
export {
  NodeType,
  HandleDirection,
  HandleLabel,
  DataType,
  ForgettingMode,
  DiagramFormat,
  DBBlockSubType,
  ContentType,
  SupportedLanguage,
  HttpMethod,
  HookType,
  HookTriggerMode,
  // Integration enums
  LLMService,
  APIServiceType,
  NotionOperation,
  // Execution enums
  ExecutionStatus,
  NodeExecutionStatus,
  EventType
} from '@dipeo/domain-models';

// Branded ID Types
export type {
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  ApiKeyID,
  DiagramID,
  ExecutionID
} from '@dipeo/domain-models';

// Core Domain Types
export type {
  Vec2,
  DomainHandle,
  DomainNode,
  DomainArrow,
  DomainPerson,
  DomainApiKey,
  DiagramMetadata,
  DomainDiagram,
  StoreDiagram,
  // Memory and config types
  MemoryConfig,
  PersonLLMConfig,
  // Tool config
  ToolConfig
} from '@dipeo/domain-models';

// Node Data Types
export type {
  BaseNodeData,
  StartNodeData,
  ConditionNodeData,
  PersonJobNodeData,
  EndpointNodeData,
  DBNodeData,
  JobNodeData,
  CodeJobNodeData,
  ApiJobNodeData,
  UserResponseNodeData,
  NotionNodeData,
  PersonBatchJobNodeData,
  HookNodeData
} from '@dipeo/domain-models';

// Execution Types
export type {
  TokenUsage,
  NodeState,
  ExecutionState,
  ExecutionOptions,
  InteractivePromptData,
  InteractiveResponse,
  ExecutionUpdate,
  NodeDefinition
} from '@dipeo/domain-models';

// Conversation Types
export type {
  PersonMemoryMessage,
  PersonMemoryState,
  PersonMemoryConfig
} from '@dipeo/domain-models';

// Utility Functions
export {
  // Handle utilities
  createHandleId,
  parseHandleId,
  getNodeHandles,
  getHandleById,
  areHandlesCompatible,
  // Diagram utilities
  createEmptyDiagram,
  diagramToStoreMaps,
  storeMapsToArrays,
  // Type conversions - moved to generated mappings
  // convertGraphQLDiagramToDomain,
  // convertGraphQLPersonToDomain,
  nodeKindToDomainType,
  domainTypeToNodeKind,
  // Type guards
  isDomainNode,
  isDomainDiagram
} from '@dipeo/domain-models';

// UI-Specific Type Augmentation
// This is the only UI-specific type that should be defined here
export type WithUI<T> = T & { 
  flipped?: boolean;
  // Allow other UI-specific properties
  [key: string]: unknown;
};

// Type guard for UI-augmented types
export function hasUIProperties<T>(obj: T | WithUI<T>): obj is WithUI<T> {
  return typeof obj === 'object' && obj !== null && 'flipped' in obj;
}

// Import types to use in function signatures
import type { 
  NodeID as NodeIDImport, 
  ArrowID as ArrowIDImport, 
  HandleID as HandleIDImport,
  PersonID as PersonIDImport, 
  ApiKeyID as ApiKeyIDImport, 
  DiagramID as DiagramIDImport,
  ExecutionID as ExecutionIDImport 
} from '@dipeo/domain-models';

// Re-export branded ID creation functions for UI convenience
export const nodeId = (id: string): NodeIDImport => id as NodeIDImport;
export const arrowId = (id: string): ArrowIDImport => id as ArrowIDImport;
export const handleId = (id: string): HandleIDImport => id as HandleIDImport;
export const personId = (id: string): PersonIDImport => id as PersonIDImport;
export const apiKeyId = (id: string): ApiKeyIDImport => id as ApiKeyIDImport;
export const diagramId = (id: string): DiagramIDImport => id as DiagramIDImport;
export const executionId = (id: string): ExecutionIDImport => id as ExecutionIDImport;