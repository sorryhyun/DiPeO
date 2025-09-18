/**
 * Centralized domain type exports from @dipeo/models
 * This file serves as the single source of truth for domain types in the frontend
 * All domain types should be imported from here, not directly from @dipeo/models
 */

// Core Enums
export {
  NodeType,
  HandleDirection,
  HandleLabel,
  DataType,
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
  // Execution enums
  Status,
  EventType
} from '@dipeo/models';


// Branded ID Types
export type {
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  ApiKeyID,
  DiagramID,
  ExecutionID
} from '@dipeo/models';

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
  // Memory and config types
  PersonLLMConfig,
  // Tool config
  ToolConfig,
  ToolSelection
} from '@dipeo/models';

// Node Data Types
// Note: Node data types are now generated locally in __generated__/models/
// They are no longer exported from @dipeo/models to avoid duplication
export type {
  BaseNodeData
} from '@dipeo/models';

// Import generated node data types
export type { StartNodeData } from '../../__generated__/models/StartNode';
export type { ConditionNodeData } from '../../__generated__/models/ConditionNode';
export type { PersonJobNodeData } from '../../__generated__/models/PersonJobNode';
export type { EndpointNodeData } from '../../__generated__/models/EndpointNode';
export { type DbNodeData as DBNodeData } from '../../__generated__/models/DbNode';
export type { CodeJobNodeData } from '../../__generated__/models/CodeJobNode';
export type { ApiJobNodeData } from '../../__generated__/models/ApiJobNode';
export type { UserResponseNodeData } from '../../__generated__/models/UserResponseNode';
export type { PersonBatchJobNodeData } from '../../__generated__/models/PersonBatchJobNode';
export type { HookNodeData } from '../../__generated__/models/HookNode';
export type { TemplateJobNodeData } from '../../__generated__/models/TemplateJobNode';
export type { JsonSchemaValidatorNodeData } from '../../__generated__/models/JsonSchemaValidatorNode';
export type { TypescriptAstNodeData } from '../../__generated__/models/TypescriptAstNode';
export type { SubDiagramNodeData } from '../../__generated__/models/SubDiagramNode';
export type { IntegratedApiNodeData } from '../../__generated__/models/IntegratedApiNode';
export type { IrBuilderNodeData } from '../../__generated__/models/IrBuilderNode';
export type { DiffPatchNodeData } from '../../__generated__/models/DiffPatchNode';

// Execution Types
export type {
  LLMUsage,
  NodeState,
  ExecutionState,
  ExecutionOptions,
  InteractivePromptData,
  InteractiveResponse,
  ExecutionUpdate,
  NodeDefinition
} from '@dipeo/models';

// Conversation Types
export type {
  PersonMemoryMessage
} from '@dipeo/models';

// Utility Functions
export {
  // Handle utilities
  createHandleId,
  parseHandleId,
  areHandlesCompatible,
  // Diagram utilities
  createEmptyDiagram,
  diagramArraysToMaps,
  diagramMapsToArrays,
  // Type conversions
  convertGraphQLDiagramToDomain,
  convertGraphQLPersonToDomain,
  nodeKindToDomainType,
  domainTypeToNodeKind,
  // Type guards
  isDomainNode,
} from '@dipeo/models';

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
} from '@dipeo/models';

// Re-export branded ID creation functions for UI convenience
export const nodeId = (id: string): NodeIDImport => id as NodeIDImport;
export const arrowId = (id: string): ArrowIDImport => id as ArrowIDImport;
export const handleId = (id: string): HandleIDImport => id as HandleIDImport;
export const personId = (id: string): PersonIDImport => id as PersonIDImport;
export const apiKeyId = (id: string): ApiKeyIDImport => id as ApiKeyIDImport;
export const diagramId = (id: string): DiagramIDImport => id as DiagramIDImport;
export const executionId = (id: string): ExecutionIDImport => id as ExecutionIDImport;
